#!/usr/bin/env python3
"""
reader.py — abre páginas da Gray Swan Arena (ou qualquer site com login) com um
navegador controlado (Playwright) e salva o conteúdo de cada página em Markdown,
pronto para leitura por agentes (Claude, etc.).

Comandos:
  login  <url>            abre uma janela visível para você fazer login; a sessão
                          fica salva em browser_profile/ e é reutilizadas pelos
                          outros comandos.
  links  <url-listagem>   lista as URLs encontradas na página (não baixa nada).
  fetch  <url-listagem>   extrai os links da listagem, abre cada um e salva o
                          conteúdo em <out>/*.md (+ manifest.json).
  open   <url>            baixa uma única URL e salva em <out>/*.md.

Exemplos (Arena):
  .venv/bin/python reader.py login https://app.grayswan.ai
  .venv/bin/python reader.py links "https://app.grayswan.ai/arena" --match challenge
  .venv/bin/python reader.py fetch "https://app.grayswan.ai/arena" --match challenge --out pages
  .venv/bin/python reader.py open "https://app.grayswan.ai/arena/challenge/x?batchGroupId=y"
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urlparse

from playwright.sync_api import TimeoutError as PWTimeoutError
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = PROJECT_DIR / "browser_profile"
DEFAULT_OUT = PROJECT_DIR / "pages"

# Ordem de preferência para achar o conteúdo principal da página.
CONTENT_SELECTORS = ["main", "article", "[role='main']", "#content", ".content", "body"]


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


def open_context(p, headed=False):
    """Abre o Chromium com perfil persistente — é o que mantém o login salvo."""
    return p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=not headed,
        viewport={"width": 1440, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )


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
            const h1 = document.querySelector('h1');
            return {
                title: document.title || '',
                h1: h1 ? (h1.innerText || '').trim() : '',
                selector: chosen.sel,
                text: chosen.t,
            };
        }""",
        content_selector,
    )


def save_page(out_dir, url, data, listing_url=""):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    title = data.get("h1") or data.get("title") or url
    body = data.get("text") or ""
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
        "---\n\n"
        f"# {title}\n\n{body}\n"
    )
    fpath.write_text(front, encoding="utf-8")
    return fpath, len(body)


def fetch_one(ctx, url, out_dir, content_selector=None, settle=2.0, wait_selector=None, listing_url=""):
    page = ctx.new_page()
    try:
        goto(page, url, settle)
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=15_000)
            except PWTimeoutError:
                pass
        data = extract_page(page, content_selector)
        return save_page(out_dir, url, data, listing_url)
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def cmd_login(args):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=False, viewport={"width": 1280, "height": 900}
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print(f"Abrindo {args.url}")
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=45_000)
        except PWTimeoutError:
            pass
        print("\n>> Faca o login na janela do navegador que acabou de abrir.")
        print(">> Quando a pagina mostrar voce logado, volte ao terminal.")
        try:
            if args.timeout:
                print(f">> A janela fecha automaticamente em {args.timeout}s.")
                time.sleep(args.timeout)
            else:
                input(">> Pressione Enter aqui para salvar a sessao e fechar... ")
        except (KeyboardInterrupt, EOFError):
            pass
        ctx.close()
    print(f"\nSessao salva em: {PROFILE_DIR}")


def cmd_links(args):
    match = re.compile(args.match) if args.match else None
    exclude = re.compile(args.exclude) if args.exclude else None
    with sync_playwright() as p:
        ctx = open_context(p, args.headed)
        try:
            page = ctx.new_page()
            print(f"Abrindo {args.url} ...")
            goto(page, args.url, args.settle)
            links = collect_links(
                page, match, exclude, same_origin=not args.any_origin, base_url=args.url
            )
            page.close()
        finally:
            ctx.close()

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

    with sync_playwright() as p:
        ctx = open_context(p, args.headed)
        try:
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
        finally:
            ctx.close()

    ok = sum(1 for v in manifest.values() if v.get("status") == "ok")
    print(f"\nPronto. {ok} pagina(s) acumuladas em {out_dir}/")
    print(f"Indice: {out_dir}/manifest.json")


def cmd_open(args):
    out_dir = Path(args.out)
    manifest = load_manifest(out_dir)
    with sync_playwright() as p:
        ctx = open_context(p, args.headed)
        try:
            fpath, chars = fetch_one(
                ctx, normalize_url(args.url), out_dir,
                content_selector=args.content_selector,
                settle=args.settle,
                wait_selector=args.wait_selector,
            )
        finally:
            ctx.close()
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

    sp = sub.add_parser("login", help="abre o navegador para voce fazer login (uma vez)")
    sp.add_argument("url", help="URL inicial (ex.: https://app.grayswan.ai)")
    sp.add_argument("--timeout", type=int, default=0,
                    help="fecha sozinho apos N segundos, em vez de esperar Enter")
    sp.set_defaults(func=cmd_login)

    sp = sub.add_parser("links", help="lista as URLs encontradas numa pagina")
    sp.add_argument("url")
    sp.add_argument("--match", help="regex: so links cuja URL casa (ex.: challenge)")
    sp.add_argument("--exclude", help="regex: pula links que casarem")
    sp.add_argument("--any-origin", action="store_true",
                    help="inclui links de outros dominios (default: mesmo dominio)")
    sp.add_argument("--limit", type=int, help="mostra no maximo N links")
    sp.add_argument("--settle", type=float, default=2.0,
                    help="segundos de espera apos o carregamento (default: 2)")
    sp.add_argument("--headed", action="store_true", help="mostra o navegador")
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
    sp.add_argument("--headed", action="store_true", help="mostra o navegador (debug)")
    sp.add_argument("--content-selector", help="extrai o texto apenas deste seletor CSS")
    sp.add_argument("--wait-selector", help="espera este seletor CSS aparecer antes de extrair")
    sp.set_defaults(func=cmd_fetch)

    sp = sub.add_parser("open", help="salva uma unica URL em .md")
    sp.add_argument("url")
    sp.add_argument("--out", default=str(DEFAULT_OUT))
    sp.add_argument("--settle", type=float, default=2.0)
    sp.add_argument("--headed", action="store_true")
    sp.add_argument("--content-selector")
    sp.add_argument("--wait-selector")
    sp.set_defaults(func=cmd_open)

    return ap


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
