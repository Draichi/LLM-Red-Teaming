#!/usr/bin/env python3
"""intake_probe.py — extrai dados de intake de UM cenário da Arena via DOM.

Somente leitura/navegação não-submissora, conforme README do grayswan-reader:
- clica no cartão do cenário (button), "See success criteria", fecha o painel,
  abre "New injection", escolhe opções role=option nos seletores site/action,
  abre menu Marker clicando apenas em grupos (aria-haspopup=menu).
- NUNCA preenche campos, nunca clica Launch/Submit/Delete/Upload/Use template.

Uso: .venv/bin/python intake_probe.py WB3S1 "Retry Budget Merge Request"
Saída: pages/intake/<code>.json
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from reader import browser_session

EVENT_URL = "https://app.grayswan.ai/arena/challenge/ipi-black-2026"
OUT_DIR = Path(__file__).resolve().parent / "pages" / "intake"

# Filtro estreito para NOMES de opções de site/action: selecionar uma option de
# listbox apenas renderiza o formulário — não submete nada. Palavras como
# delete/send/post/reply são nomes legítimos de actions e devem ser lidas.
BANNED_OPTION = re.compile(r"submit|launch", re.I)


def log(actions, kind, **kw):
    actions.append({"kind": kind, **kw})
    print(f"[probe] {kind}: {kw}", flush=True)


def norm(s):
    return re.sub(r"[\s\u200b\u200c\u200d]+", " ", s or "").strip()


def click_visible(locator, timeout=3_000):
    """Clica o primeiro match VISÍVEL de um locator (a UI duplica controles
    para mobile/desktop; .first pode estar hidden)."""
    n = locator.count()
    last = None
    for i in range(n):
        el = locator.nth(i)
        try:
            if el.is_visible():
                el.click(timeout=timeout)
                return i
        except Exception as e:
            last = e
    raise RuntimeError(f"click_visible: nenhum match visível ({n} matches): {last}")


def main_inner(page, code, name, actions, out):
    page.goto(EVENT_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(4000)

    body = norm(page.locator("body").inner_text())
    out["event_wave_header"] = "Wave 3" if "Wave 3" in body else "?"
    log(actions, "page_loaded", wave=out["event_wave_header"])

    # --- 1. achar e clicar o cartão do cenário -------------------------------
    cards = page.locator("main button")
    target = None
    for i in range(cards.count()):
        el = cards.nth(i)
        t = norm(el.inner_text())
        if t.startswith(code) and name.split(" | ")[0].lower() in t.lower():
            target = el
            out["card_text"] = t
            break
    if target is None:
        raise RuntimeError(f"cartão do cenário {code} não encontrado")
    log(actions, "card_found", text=out["card_text"][:120])
    target.click(timeout=5_000)
    page.wait_for_selector("#world-injection-0-site", timeout=20_000)
    page.wait_for_timeout(1500)

    td_text = norm(page.locator("main").inner_text())
    if code not in td_text:
        raise RuntimeError(f"Task Details não mostra {code} após clique no cartão")
    out["task_details_heading"] = code
    log(actions, "task_details_verified", heading=out["task_details_heading"])

    # --- 2. Harmful task / Benign task description ----------------------------
    def section_after(label):
        return page.evaluate(
            """(label) => {
                const els = [...document.querySelectorAll('main p, main div, main span')];
                const lab = els.find(e => e.children.length === 0
                    && (e.innerText || '').trim().toUpperCase() === label);
                if (!lab) return null;
                let n = lab.nextElementSibling;
                while (n && !(n.innerText || '').trim()) n = n.nextElementSibling;
                if (!n) {
                    let p = lab.parentElement;
                    if (p) {
                        const kids = [...p.children];
                        const idx = kids.indexOf(lab);
                        for (let i = idx + 1; i < kids.length; i++) {
                            if ((kids[i].innerText || '').trim()) return kids[i].innerText.trim();
                        }
                    }
                    return null;
                }
                return (n.innerText || '').trim();
            }""",
            label,
        )

    out["harmful_task"] = section_after("HARMFUL TASK")
    out["benign_task"] = section_after("BENIGN TASK DESCRIPTION")
    log(actions, "tasks_extracted",
        harmful=norm(out["harmful_task"])[:80], benign=norm(out["benign_task"])[:80])

    # --- 3. See success criteria ----------------------------------------------
    # O painel de critérios é um painel inline (#workspaceCriteriaPanel), não um
    # dialog: alterna visível/oculto pelo botão "See success criteria".
    crit_text = None
    for attempt in range(14):
        panel = page.evaluate(
            """() => {
                const el = document.querySelector('#workspaceCriteriaPanel');
                if (!el) return null;
                const b = el.getBoundingClientRect();
                return {text: (el.innerText || '').trim(),
                        visible: b.width > 0 && b.height > 0};
            }"""
        )
        if panel and "Objective" in (panel["text"] or "") and panel["visible"]:
            crit_text = panel["text"]
            out["criteria_selector"] = "#workspaceCriteriaPanel"
            break
        if attempt == 0:
            try:
                click_visible(page.locator(
                    "main button", has_text=re.compile(r"See success criteria", re.I)))
            except Exception as e:
                log(actions, "criteria_click_failed", err=str(e)[:120])
        page.wait_for_timeout(1000)
    if not crit_text:
        crit_text = ""
    out["success_criteria_text"] = crit_text
    log(actions, "criteria_captured", chars=len(crit_text))

    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    log(actions, "criteria_closed")

    # --- 4. contadores globais -------------------------------------------------
    main_text = norm(page.locator("main").inner_text())
    m = re.search(r"New injection \((\d+)/(\d+) max\)", main_text)
    out["new_injection_counter"] = m.group(0) if m else None
    out["max_slots"] = int(m.group(2)) if m else None
    out["used_slots"] = int(m.group(1)) if m else None
    m = re.search(r"LAUNCH · (\d+)", main_text)
    out["launch_cost"] = m.group(1) if m else None
    m = re.search(r"Energy (\d+) of (\d+), plus (\d+) bonus", main_text)
    out["energy"] = m.groups() if m else None
    log(actions, "counters", **{k: out.get(k) for k in
        ("new_injection_counter", "launch_cost", "energy")})

    # --- 5. leitor de campos de um injection index ----------------------------
    def read_fields(idx):
        return page.evaluate(
            """(idx) => {
                const fields = [];
                const els = [...document.querySelectorAll(
                    `[id^='world-injection-${idx}-field-']`)];
                for (const el of els) {
                    const name = (el.id.match(/^world-injection-\\d+-field-(.+)$/) || [])[1] || '';
                    const lab = el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
                    const b = el.getBoundingClientRect();
                    fields.push({
                        id: el.id, name,
                        tag: el.tagName.toLowerCase(),
                        type: el.getAttribute('type') || el.getAttribute('role') || '',
                        value: ('value' in el) ? el.value : null,
                        placeholder: el.getAttribute('placeholder'),
                        maxLength: el.getAttribute('maxlength'),
                        required_attr: el.required === true || el.getAttribute('required') !== null,
                        aria_required: el.getAttribute('aria-required'),
                        label_text: lab ? lab.innerText.trim() : null,
                        visible: b.width > 0 && b.height > 0,
                    });
                }
                return fields;
            }""",
            idx,
        )

    def card_text(idx):
        return page.evaluate(
            """(idx) => {
                const site = document.querySelector(`#world-injection-${idx}-site`);
                if (!site) return null;
                let el = site;
                for (let hops = 0; hops < 8 && el.parentElement; hops++) {
                    el = el.parentElement;
                    const t = (el.innerText || '').trim();
                    if (t && t.length > 20) return t.slice(0, 900);
                }
                return (el.innerText || '').trim().slice(0, 900);
            }""",
            idx,
        )

    f0 = read_fields(0)
    c0 = card_text(0)
    out["mandatory_injection"] = {
        "site_trigger_aria": page.locator("#world-injection-0-site").get_attribute("aria-label"),
        "action_trigger_aria": page.locator("#world-injection-0-action").get_attribute("aria-label"),
        "card_text": c0,
        "fields": f0,
    }
    log(actions, "mandatory_read", fields=[f["name"] for f in f0])

    # --- 6. menu Marker (grupos somente) ---------------------------------------
    marker_summary = {}
    mk_btn = page.locator('main button[aria-label^="Insert a marker into"]')
    if mk_btn.count():
        click_visible(mk_btn, timeout=5_000)
        page.wait_for_timeout(1500)
        menu_dump = """() => {
            const out = [];
            for (const el of document.querySelectorAll('[role="menuitem"]')) {
                const t = (el.innerText || '').trim();
                if (!t || t.length > 80) continue;
                const b = el.getBoundingClientRect();
                out.push({text: t.slice(0, 70),
                          haspopup: el.getAttribute('aria-haspopup') === 'menu',
                          visible: b.width > 0 && b.height > 0});
            }
            return out;
        }"""
        initial = page.evaluate(menu_dump)
        marker_summary["groups"] = {}
        for item in initial:
            if item["haspopup"] and item.get("visible"):
                marker_summary["groups"][item["text"]] = None
        for gname in list(marker_summary["groups"].keys()):
            try:
                # abordagem por índice: filtrar por texto pode pegar camada
                # oculta de animação do radix; itera todos e casa pelo texto
                clicked = False
                groups = page.locator("[aria-haspopup='menu']")
                for gi in range(groups.count()):
                    gt = norm(groups.nth(gi).inner_text())
                    if gt != gname:
                        continue
                    try:
                        groups.nth(gi).click(timeout=3_000)
                        clicked = True
                        break
                    except Exception:
                        continue
                if not clicked:
                    raise RuntimeError("grupo não clicável")
                page.wait_for_timeout(1200)
                subs = page.evaluate(menu_dump)
                leaves = [i["text"] for i in subs if not i["haspopup"] and i.get("visible")]
                marker_summary["groups"][gname] = leaves
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)
                click_visible(page.locator('main button[aria-label^="Insert a marker into"]'), timeout=3_000)
                page.wait_for_timeout(1000)
            except Exception as e:
                marker_summary["groups"][gname] = f"ERRO: {str(e)[:100]}"
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
        marker_summary["field_value_after"] = page.evaluate(
            "() => document.querySelector('#world-injection-0-field-body')?.value ?? null")
    out["marker_menu"] = marker_summary
    log(actions, "marker_menu", groups={k: (v if isinstance(v, str) else len(v or []))
                                        for k, v in (marker_summary.get("groups") or {}).items()},
        field_value_after=marker_summary.get("field_value_after"))

    # --- 7. New injection: enumerar sites/actions e campos --------------------
    click_visible(page.locator("main button", has_text=re.compile(r"New injection \(")))
    page.wait_for_timeout(2000)
    log(actions, "new_injection_opened")

    def read_open_options():
        return page.evaluate(
            """() => {
                const els = [...document.querySelectorAll('[role="option"]')];
                return els.map(e => ({
                    text: (e.innerText || '').trim(),
                    disabled: e.getAttribute('aria-disabled') === 'true',
                })).filter(o => o.text);
            }"""
        )

    def click_option(wanted):
        opts = page.locator("[role='option']")
        for i in range(opts.count()):
            if wanted in (opts.nth(i).inner_text() or ""):
                opts.nth(i).click(timeout=3_000)
                return True
        return False

    idxs = page.evaluate(
        """() => [...new Set([...document.querySelectorAll('[id^="world-injection-"]')]
            .map(e => (e.id.match(/^world-injection-(\\d+)-/) || [])[1]).filter(Boolean))]"""
    )
    new_idx = max(int(i) for i in idxs) if idxs else 1
    out["new_injection_index"] = new_idx
    base = f"world-injection-{new_idx}"

    surfaces = {}
    try:
        page.locator(f"#{base}-site").click(timeout=5_000)
        page.wait_for_timeout(900)
        site_opts = read_open_options()
        out["site_options"] = site_opts
        log(actions, "site_options", n=len(site_opts),
            texts=[norm(o["text"]) for o in site_opts])
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        for so in site_opts:
            site_name = norm(so["text"])
            if BANNED_OPTION.search(site_name):
                log(actions, "site_skipped_banned", site=site_name)
                continue
            surfaces[site_name] = {"disabled_option": so["disabled"], "actions": {}}
            page.locator(f"#{base}-site").click(timeout=5_000)
            page.wait_for_timeout(700)
            if not click_option(so["text"]):
                log(actions, "site_option_click_failed", site=site_name)
                page.keyboard.press("Escape")
                continue
            page.wait_for_timeout(1200)

            act_combo = page.locator(f"#{base}-action")
            act_disabled = not act_combo.is_enabled()
            act_label = norm(act_combo.inner_text())
            if act_disabled:
                act_opts = [{"text": act_label, "disabled": True}]
            else:
                try:
                    act_combo.click(timeout=5_000)
                    page.wait_for_timeout(900)
                    act_opts = read_open_options()
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                except Exception:
                    act_opts = []
            out.setdefault("action_options_by_site", {})[site_name] = [
                norm(o["text"]) for o in act_opts]
            log(actions, "action_options", site=site_name, n=len(act_opts),
                texts=[norm(o["text"]) for o in act_opts])

            for ao in act_opts:
                act_name = norm(ao["text"])
                if BANNED_OPTION.search(act_name):
                    surfaces[site_name]["actions"][act_name] = {"banned_name": True}
                    continue
                if not ao.get("disabled"):
                    try:
                        act_combo.click(timeout=5_000)
                        page.wait_for_timeout(700)
                        if not click_option(ao["text"]):
                            raise RuntimeError("option not clickable")
                    except Exception as e:
                        log(actions, "action_click_failed", action=act_name, err=str(e)[:120])
                        surfaces[site_name]["actions"][act_name] = {"click_error": str(e)[:200]}
                        page.keyboard.press("Escape")
                        continue
                # espera os campos aparecerem
                try:
                    page.wait_for_selector(f"[id^='{base}-field-']", timeout=8_000)
                except Exception:
                    log(actions, "action_fields_timeout", action=act_name)
                page.wait_for_timeout(800)

                fields = read_fields(new_idx)
                ctext = card_text(new_idx)
                caps = sorted(set(re.findall(
                    r"\d+ of \d+ .{0,120}? injections used", norm(ctext or ""))))
                surfaces[site_name]["actions"][act_name] = {
                    "option_disabled": ao.get("disabled", False),
                    "card_text": ctext,
                    "caps_visible": caps,
                    "fields": fields,
                }
                log(actions, "action_fields", site=site_name, action=act_name,
                    fields=[f["name"] for f in fields], caps=caps)
                page.wait_for_timeout(400)
    finally:
        page.goto(EVENT_URL, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(4000)
        log(actions, "page_reloaded_discard_unsaved")

    out["surfaces"] = surfaces

    post = norm(page.locator("main").inner_text())
    mpost = re.search(r"New injection \((\d+)/(\d+) max\)", post)
    out["post_injection_counter"] = mpost.group(0) if mpost else None
    out["post_injection_labels_count"] = len(re.findall(r"Injection \d+ site:", post))
    log(actions, "post_state", **{
        "counter": out["post_injection_counter"],
        "injection_labels": out["post_injection_labels_count"],
    })


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: intake_probe.py <CODE> <NOME>")
    code, name = sys.argv[1], sys.argv[2]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"scenario_code": code, "scenario_name": name,
           "event_url": EVENT_URL, "actions": []}
    with sync_playwright() as p, browser_session(p) as ctx:
        page = ctx.new_page()
        try:
            main_inner(page, code, name, out["actions"], out)
        finally:
            page.close()
    jpath = OUT_DIR / f"{code.lower()}.json"
    jpath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo: {jpath}")


if __name__ == "__main__":
    main()
