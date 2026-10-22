#!/usr/bin/env python3
"""
reader.py — abre páginas da Gray Swan Arena (ou qualquer site) usando o SEU
navegador (Arc/Chrome) já logado, via porta de debug, e salva o conteúdo de
cada página em Markdown, pronto para leitura por agentes (Claude, etc.).

Requisito (única vez por sessão do navegador): relançar o Arc com a porta de
debug — o Chromium só aceita a flag na inicialização:

  osascript -e 'quit app "Arc"'; open -na Arc --args --remote-debugging-port=9222

A ferramenta anexa-se ao navegador em execução, usa a sua sessão real (não há
`login`: se o site pedir login, é o navegador que está sem sessão — faça nela),
abre/fecha abas e, no fim, apenas desconecta. Read-only por padrão; o único
clique que existe é o `--expand` (restrito, ver abaixo).

Comandos:
  links  <url-listagem>   lista as URLs encontradas na página (não baixa nada).
  fetch  <url-listagem>   extrai os links da listagem, abre cada um e salva o
                          conteúdo em <out>/*.md (+ manifest.json).
  open   <url>            baixa uma única URL e salva em <out>/*.md.

Exemplos (Arena):
  .venv/bin/python reader.py links "https://app.grayswan.ai/arena" --match challenge
  .venv/bin/python reader.py fetch "https://app.grayswan.ai/arena" --match challenge
  .venv/bin/python reader.py open "https://app.grayswan.ai/arena/challenge/x?chatId=y" \
      --capture-api --expand
"""

import argparse
import hashlib
import json
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urlparse

from playwright.sync_api import TimeoutError as PWTimeoutError
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = PROJECT_DIR / "pages"

# Ordem de preferência para achar o conteúdo principal da página.
CONTENT_SELECTORS = ["main", "article", "[role='main']", "#content", ".content", "body"]

CDP_DEFAULT_PORT = 9222

# Clique restrito autorizado pelo operador (2026-10-22): expandir SOMENTE
# controles de disclosure ("Expand to see details"). O app ignora el.click()
# sintético (evento isTrusted:false), então o clique é dado pelo Playwright
# (input real via CDP) NO ELEMENTO encontrado pelo seletor abaixo — a área
# clicada é a bounding box do próprio controle whitelistado, nunca vizinho.
# Whitelist + blacklist dupla de controles de ação/submissão. 1 clique por
# controle; marca data-gsr-expanded para não re-clicar numa 2ª passada.
EXPAND_FIND_JS = """
() => {
    const banned = /submit|break|send|post|reply|delete|confirm|place|order|pay|refund/i;
    const allowed = /expand|show more|ver mais|detalhes/i;
    const targets = [];
    for (const leaf of document.querySelectorAll('p, span, div, button, summary')) {
        if (leaf.children.length > 1) continue;
        const t = (leaf.innerText || '').trim();
        if (!t || t.length > 80 || !allowed.test(t) || banned.test(t)) continue;
        let target = leaf, hops = 0, clickable = null;
        while (target && hops < 5) {
            const cls = String(target.className || '');
            if (cls.includes('cursor-pointer') || target.getAttribute('role') === 'button'
                || target.tagName === 'BUTTON' || target.tagName === 'SUMMARY') {
                clickable = target; break;
            }
            target = target.parentElement; hops++;
        }
        const el = clickable || leaf.parentElement;
        if (!el) continue;
        if (el.closest('[data-gsr-expanded]')) continue;  // já clicado nesta visita
        const et = (el.innerText || '').trim();
        if (banned.test(et)) continue;              // contêiner não pode citar ação
        if (el.getAttribute('aria-expanded') === 'true') continue;
        if (el.type === 'submit') continue;
        // descarta alvo contido num alvo já coletado (mesmo controle)
        if (!targets.some(kept => kept.contains(el))) targets.push(el);
    }
    return targets.slice(0, 30);
}
"""


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def slugify(text, max_len=60):
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len].strip("-") or "pagina"


def url_key(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def normalize_url(url):
    url, _ = urldefrag(url)
    return url


def load_manifest(out_dir):
    path = Path(out_dir) / "manifest.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def save_manifest(out_dir, manifest):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@contextmanager
def browser_session(p, cdp_port=CDP_DEFAULT_PORT):
    """Anexa ao navegador do operador (Arc/Chrome) via porta de debug.

    Usa a sessão real do navegador (nada de login/perfil embutido) e, no fim,
    apenas desconecta — o navegador continua aberto, nada é fechado nele.
    """
    try:
        browser = p.chromium.connect_over_cdp(
            f"http://127.0.0.1:{cdp_port}", timeout=10_000
        )
    except Exception as exc:
        raise SystemExit(
            f"Nao consegui conectar em 127.0.0.1:{cdp_port} ({type(exc).__name__}).\n"
            "Relance o Arc com a porta de debug e tente de novo:\n"
            "  osascript -e 'quit app \"Arc\"'; "
            f"open -na Arc --args --remote-debugging-port={cdp_port}"
        )
    try:
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        yield ctx
    finally:
        browser.close()  # só desconecta — o navegador do operador fica aberto


def goto(page, url, settle=2.0):
    """Navega e espera a página assentar (bom para SPAs como a Arena)."""
    try:
        page.goto(url, wait_until="networkidle", timeout=45_000)
    except PWTimeoutError:
        # Páginas com polling/WebSocket nunca chegam ao "networkidle";
        # seguimos com o que já carregou.
        pass
    if settle > 0:
        page.wait_for_timeout(int(settle * 1000))


# ---------------------------------------------------------------------------
# Extração
# ---------------------------------------------------------------------------

def collect_links(page, match=None, exclude=None, same_origin=True, base_url=""):
    """Extrai {url, texto} de todos os <a> visíveis, com dedupe e filtros."""
    raw = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({href: e.href, text: (e.innerText || e.getAttribute('aria-label') || '').trim()}))",
    )
    base_origin = urlparse(base_url).netloc
    seen, out = set(), []
    for item in raw:
        url = normalize_url(item["href"])
        if not url.startswith("http"):
            continue
        if same_origin and urlparse(url).netloc != base_origin:
            continue
        if url in seen:
            continue
        seen.add(url)
        if match and not match.search(url):
            continue
        if exclude and exclude.search(url):
            continue
        out.append({"url": url, "text": item["text"]})
    return out


def extract_page(page, content_selector=None):
    """Retorna {title, h1, selector, text} priorizando containers de conteúdo."""
    return page.evaluate(
        """(contentSelector) => {
            const defaults = ['main', 'article', "[role='main']", '#content', '.content', 'body'];
            const sels = contentSelector ? [contentSelector, ...defaults] : defaults;
            const candidates = [];
            for (const sel of sels) {
                const el = document.querySelector(sel);
                const t = el ? (el.innerText || '').trim() : '';
                if (t) candidates.push({sel, t});
                if (t.length >= 200 && sel !== 'body') break;
            }
            const chosen =
                candidates.find(c => c.t.length >= 200 && c.sel !== 'body') ||
                candidates.find(c => c.sel !== 'body') ||
                candidates.find(c => c.sel === 'body') ||
                {sel: '(vazio)', t: ''};
            const chosenEl = document.querySelector(chosen.sel);
            const full = chosenEl && chosenEl.textContent
                ? chosenEl.textContent.replace(/\\s+/g, ' ').trim() : '';
            const h1 = document.querySelector('h1');
            return {
                title: document.title || '',
                h1: h1 ? (h1.innerText || '').trim() : '',
                selector: chosen.sel,
                text: chosen.t,
                full: full,
            };
        }""",
        content_selector,
    )


def save_page(out_dir, url, data, listing_url=""):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    title = data.get("h1") or data.get("title") or url
    body = data.get("text") or ""
    full = data.get("full") or ""
    hidden = ""
    if len(full) > len(body) + 500:
        hidden = (
            "\n\n## Conteudo oculto/colapsado no DOM (textContent)\n\n"
            + full[:400_000] + "\n"
        )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fpath = out_dir / f"{slugify(title)}-{url_key(url)}.md"
    front = (
        "---\n"
        f"url: {url}\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"fetched_at: {now}\n"
        + (f"listing: {listing_url}\n" if listing_url else "")
        + f"content_selector: {data.get('selector')}\n"
        f"chars: {len(body)}\n"
        + (f"hidden_chars: {len(full)}\n" if hidden else "")
        + "---\n\n"
        f"# {title}\n\n{body}{hidden}\n"
    )
    fpath.write_text(front, encoding="utf-8")
    return fpath, len(body)


def attach_api_capture(page, out_dir):
    """Grava passivamente as respostas JSON da SPA em <out>/api/ (zero interação).

    Complementar ao --expand: o detalhe de tool calls é renderizado client-side
    (v-if) e não vem por XHR, mas payloads e dados de listagem da Arena que
    trafegam por rede acabam capturados aqui. Best-effort, nunca atrapalha.
    """
    cap = Path(out_dir) / "api"
    cap.mkdir(parents=True, exist_ok=True)

    def on_response(resp):
        try:
            if "json" not in (resp.headers.get("content-type") or ""):
                return
            url = resp.url
            if "grayswan" not in url:
                return
            body = resp.text()
            key = url_key(url)
            name = f"{slugify(urlparse(url).path.replace('/', ' ') or 'api', 40)}-{key}.json"
            (cap / name).write_text(body, encoding="utf-8")
        except Exception:
            pass  # captura é best-effort; nunca atrapalha a extração

    page.on("response", on_response)


def expand_controls(page, passes=2):
    """Clique restrito (autorizado 2026-10-22): expande disclosure controls.

    Encontra alvos com EXPAND_FIND_JS e clica via Playwright (input real, já
    que o app filtra evento sintético). 1 clique por controle, máx. 2 passadas
    para pegar controles que só aparecem depois do 1º. Best-effort.
    """
    total = 0
    for _ in range(passes):
        try:
            arr = page.evaluate_handle(EXPAND_FIND_JS)
            count = arr.evaluate("els => els.length")
        except Exception:
            return total
        if not count:
            break
        for i in range(count):
            try:
                elh = arr.get_property(str(i))
                elh.evaluate("el => el.setAttribute('data-gsr-expanded', '1')")
                elh.click(timeout=3_000)  # input real: mesmo elemento, sem vizinho
                elh.dispose()
                total += 1
            except Exception:
                pass  # alvo pode ter saído do DOM após re-render; segue
        page.wait_for_timeout(1_500)  # render do que acabou de abrir
        try:
            arr.dispose()
        except Exception:
            pass
    if total:
        page.wait_for_timeout(2_000)  # render final
    return total


def fetch_one(ctx, url, out_dir, content_selector=None, settle=2.0, wait_selector=None, listing_url="", capture_api=False, expand=False):
    page = ctx.new_page()
    try:
        if capture_api:
            attach_api_capture(page, out_dir)
        goto(page, url, settle)
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=15_000)
            except PWTimeoutError:
                pass
        if expand:
            try:
                expand_controls(page)
            except Exception:
                pass  # expansão é best-effort; extração segue sem ela
        data = extract_page(page, content_selector)
        return save_page(out_dir, url, data, listing_url)
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def cmd_links(args):
    match = re.compile(args.match) if args.match else None
    exclude = re.compile(args.exclude) if args.exclude else None
    with sync_playwright() as p, browser_session(p, args.cdp_port) as ctx:
        page = ctx.new_page()
        print(f"Abrindo {args.url} ...")
        goto(page, args.url, args.settle)
        links = collect_links(
            page, match, exclude, same_origin=not args.any_origin, base_url=args.url
        )
        page.close()

    if args.limit:
        links = links[: args.limit]
    if not links:
        print("\nNenhuma URL encontrada. Dicas: tire o --match para ver todos os")
        print("links, ou aumente --settle se a pagina for lenta para carregar.")
        return
    print(f"\n{len(links)} URL(s) encontrada(s):\n")
    for i, item in enumerate(links, 1):
        label = f" — {item['text']}" if item["text"] else ""
        print(f"{i:3}. {item['url']}{label}")
    print("\nPara baixar o conteudo de todas, rode 'fetch' com o mesmo --match.")


def cmd_fetch(args):
    match = re.compile(args.match) if args.match else None
    exclude = re.compile(args.exclude) if args.exclude else None
    out_dir = Path(args.out)
    manifest = load_manifest(out_dir)
    listing = normalize_url(args.url)

    with sync_playwright() as p, browser_session(p, args.cdp_port) as ctx:
        page = ctx.new_page()
        print(f"Abrindo listagem: {args.url}")
        goto(page, args.url, args.settle)
        links = [i["url"] for i in collect_links(
            page, match, exclude, same_origin=not args.any_origin, base_url=args.url
        )]
        page.close()

        links = [u for u in links if u != listing]
        if args.limit:
            links = links[: args.limit]
        print(f"{len(links)} URL(s) na fila.\n")

        for i, url in enumerate(links, 1):
            if not args.force and manifest.get(url, {}).get("status") == "ok":
                print(f"[{i}/{len(links)}] ja salvo, pulando: {url}")
                continue
            try:
                fpath, chars = fetch_one(
                    ctx, url, out_dir,
                    content_selector=args.content_selector,
                    settle=args.settle,
                    wait_selector=args.wait_selector,
                    listing_url=args.url,
                    capture_api=args.capture_api,
                    expand=args.expand,
                )
                manifest[url] = {
                    "file": str(fpath),
                    "title": fpath.name,
                    "chars": chars,
                    "status": "ok" if chars else "vazio",
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                print(f"[{i}/{len(links)}] {url} -> {fpath.name} ({chars} chars)")
            except Exception as exc:  # uma página que falhou não para o resto
                manifest[url] = {
                    "status": f"erro: {exc}",
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                print(f"[{i}/{len(links)}] ERRO em {url}: {exc}", file=sys.stderr)
            save_manifest(out_dir, manifest)
            if args.delay and i < len(links):
                time.sleep(args.delay)

    ok = sum(1 for v in manifest.values() if v.get("status") == "ok")
    print(f"\nPronto. {ok} pagina(s) acumuladas em {out_dir}/")
    print(f"Indice: {out_dir}/manifest.json")


def cmd_open(args):
    out_dir = Path(args.out)
    manifest = load_manifest(out_dir)
    with sync_playwright() as p, browser_session(p, args.cdp_port) as ctx:
        fpath, chars = fetch_one(
            ctx, normalize_url(args.url), out_dir,
            content_selector=args.content_selector,
            settle=args.settle,
            wait_selector=args.wait_selector,
            capture_api=args.capture_api,
            expand=args.expand,
        )
    manifest[normalize_url(args.url)] = {
        "file": str(fpath),
        "chars": chars,
        "status": "ok" if chars else "vazio",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_manifest(out_dir, manifest)
    print(f"Salvo: {fpath} ({chars} chars)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="reader.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("links", help="lista as URLs encontradas numa pagina")
    sp.add_argument("url")
    sp.add_argument("--match", help="regex: so links cuja URL casa (ex.: challenge)")
    sp.add_argument("--exclude", help="regex: pula links que casarem")
    sp.add_argument("--any-origin", action="store_true",
                    help="inclui links de outros dominios (default: mesmo dominio)")
    sp.add_argument("--limit", type=int, help="mostra no maximo N links")
    sp.add_argument("--settle", type=float, default=2.0,
                    help="segundos de espera apos o carregamento (default: 2)")
    sp.add_argument("--cdp-port", type=int, default=CDP_DEFAULT_PORT,
                    help="porta de debug do Arc/Chrome (default: 9222)")
    sp.set_defaults(func=cmd_links)

    sp = sub.add_parser("fetch", help="extrai os links da listagem e salva cada pagina em .md")
    sp.add_argument("url", help="URL da pagina de listagem")
    sp.add_argument("--match", help="regex: so links cuja URL casa")
    sp.add_argument("--exclude", help="regex: pula links que casarem")
    sp.add_argument("--any-origin", action="store_true")
    sp.add_argument("--out", default=str(DEFAULT_OUT), help="pasta de saida (default: pages/)")
    sp.add_argument("--limit", type=int, help="baixa no maximo N paginas nesta execucao")
    sp.add_argument("--delay", type=float, default=1.0, help="pausa entre paginas, em s (default: 1)")
    sp.add_argument("--settle", type=float, default=2.0, help="espera extra por pagina, em s (default: 2)")
    sp.add_argument("--force", action="store_true", help="rebaixa paginas ja salvas")
    sp.add_argument("--cdp-port", type=int, default=CDP_DEFAULT_PORT,
                    help="porta de debug do Arc/Chrome (default: 9222)")
    sp.add_argument("--capture-api", action="store_true",
                    help="grava as respostas JSON da SPA em <out>/api/")
    sp.add_argument("--expand", action="store_true",
                    help="clique restrito: expande só controles 'Expand...' (nunca submissão)")
    sp.add_argument("--content-selector", help="extrai o texto apenas deste seletor CSS")
    sp.add_argument("--wait-selector", help="espera este seletor CSS aparecer antes de extrair")
    sp.set_defaults(func=cmd_fetch)

    sp = sub.add_parser("open", help="salva uma unica URL em .md")
    sp.add_argument("url")
    sp.add_argument("--out", default=str(DEFAULT_OUT))
    sp.add_argument("--settle", type=float, default=2.0)
    sp.add_argument("--cdp-port", type=int, default=CDP_DEFAULT_PORT,
                    help="porta de debug do Arc/Chrome (default: 9222)")
    sp.add_argument("--capture-api", action="store_true",
                    help="grava as respostas JSON da SPA em <out>/api/")
    sp.add_argument("--expand", action="store_true",
                    help="clique restrito: expande só controles 'Expand...' (nunca submissão)")
    sp.add_argument("--content-selector")
    sp.add_argument("--wait-selector")
    sp.set_defaults(func=cmd_open)

    return ap


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
