#!/usr/bin/env python3
"""lucky_probe.py — extrai intake de UM cenário DIRECT da Arena via DOM.
Somente leitura/navegação não-submissora: clica no cartão do cenário e no botão
"See success criteria"; NUNCA preenche campos nem clica Submit Break/Launch.

Uso: .venv/bin/python lucky_probe.py "<NOME DO CENÁRIO>"
Saída: pages/intake/lucky/<slug>.json
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from reader import browser_session

EVENT_URL = "https://app.grayswan.ai/arena/challenge/lucky-break-payday"
OUT_DIR = Path(__file__).resolve().parent / "pages" / "intake" / "lucky"


def norm(s):
    return re.sub(r"[\s\u200b\u200c\u200d]+", " ", s or "").strip()


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def click_visible(locator, timeout=3_000):
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
    raise RuntimeError(f"click_visible: nenhum match visível ({n}): {last}")


def main():
    name = sys.argv[1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"scenario_name": name, "event_url": EVENT_URL}
    actions = []

    with sync_playwright() as p, browser_session(p) as ctx:
        page = ctx.new_page()
        page.goto(EVENT_URL, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(4000)

        body = norm(page.locator("body").inner_text())
        m = re.search(r"LIVE\s*([A-Z]{3} \d{2} - [A-Z]{3} \d{2})", body)
        out["event_window"] = m.group(1) if m else None
        m = re.search(r"\$([\d,]+) prize pool", body)
        out["prize_pool"] = m.group(0) if m else None
        m = re.search(r"(\d+)/5 SCENARIOS SOLVED", body)
        out["scenarios_solved"] = m.group(0) if m else None

        # --- 1. clicar no cartão do cenário (button cujo texto contém o nome)
        cards = page.locator("main button")
        target = None
        for i in range(cards.count()):
            el = cards.nth(i)
            t = norm(el.inner_text())
            if name.lower() in t.lower() and len(t) < 200:
                target = el
                out["card_text"] = t
                break
        if target is None:
            raise RuntimeError(f"cartão do cenário não encontrado: {name}")
        target.click(timeout=5_000)
        page.wait_for_timeout(2500)

        out["task_details"] = norm(page.locator("main").inner_text())

        # --- 2. See success criteria (painel inline ou dialog)
        crit = None
        for attempt in range(10):
            panel = page.evaluate(
                """() => {
                    for (const sel of ['#workspaceCriteriaPanel', '[role=dialog]']) {
                        const el = document.querySelector(sel);
                        if (el) {
                            const b = el.getBoundingClientRect();
                            const t = (el.innerText || '').trim();
                            if (t && b.width > 0 && b.height > 0) return t;
                        }
                    }
                    return null;
                }"""
            )
            if panel and ("Objective" in panel or "Criteria" in panel or "Criteria" in panel):
                crit = panel
                break
            if attempt == 0:
                try:
                    click_visible(page.locator(
                        "main button", has_text=re.compile(r"See success criteria", re.I)))
                except Exception:
                    pass
            page.wait_for_timeout(1000)
        out["success_criteria"] = crit
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.wait_for_timeout(800)

        # --- 3. campos de texto/entrada visíveis (formulário de prompt)
        out["fields"] = page.evaluate(
            """() => {
                const fields = [];
                for (const el of document.querySelectorAll('main textarea, main input, main [contenteditable=true]')) {
                    const b = el.getBoundingClientRect();
                    if (!(b.width > 0 && b.height > 0)) continue;
                    const id = el.id || el.name || '';
                    const lab = id ? document.querySelector(`label[for="${id}"]`) : null;
                    fields.push({
                        id, tag: el.tagName.toLowerCase(),
                        type: el.getAttribute('type') || '',
                        placeholder: el.getAttribute('placeholder'),
                        maxLength: el.getAttribute('maxlength'),
                        aria_label: el.getAttribute('aria-label'),
                        label_text: lab ? lab.innerText.trim() : null,
                        contenteditable: el.getAttribute('contenteditable'),
                    });
                }
                return fields;
            }"""
        )

        # --- 4. contadores: energia, submissions, botões de ação (labels only)
        main_text = norm(page.locator("main").inner_text())
        for pat, key in [
            (r"Energy (\d+) of (\d+)(?:\.|, plus (\d+) bonus)?", "energy"),
            (r"(\d+)\s*/\s*(\d+) breaks", "breaks_counter"),
            (r"Model Submissions\s*(\d+)", "model_submissions"),
        ]:
            m = re.search(pat, main_text)
            out[key] = m.group(0) if m else None
        out["action_buttons"] = page.evaluate(
            """() => [...new Set([...document.querySelectorAll('main button')]
                .filter(b => b.offsetParent !== null)
                .map(b => (b.innerText || '').trim()).filter(t => t && t.length < 60))]"""
        )
        out["markers_visible"] = page.evaluate(
            """() => [...new Set([...document.querySelectorAll('main [aria-label]')]
                .map(e => e.getAttribute('aria-label'))
                .filter(a => a && /marker/i.test(a)))]"""
        )

    out_path = OUT_DIR / f"{slugify(name)}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Salvo: {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
