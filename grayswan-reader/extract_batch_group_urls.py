#!/usr/bin/env python3
"""Extrai (modelo, run URL) dos blocos de run de um batch group da Arena.

Somente leitura: abre a URL, espera os blocos de batch renderizarem e lista o
innerText + hrefs de cada <li> sob cada bloco. Uso:

    .venv/bin/python extract_batch_group_urls.py "<url-do-batch-group>"

Sem argumento, usa o batch group wb3s1 v3 de 2026-11-02 como default.
Pode ser importado pelo batch_intake.py para o pipeline completo.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright
from reader import browser_session

DEFAULT_URL = (
    "https://app.grayswan.ai/arena/challenge/ipi-black-2026"
    "?batchGroupId=c72b62d99d487578130e34c085390a8c"
)

EXTRACT_JS = """
() => {
    const root = document.querySelector('#chatElement');
    if (!root) return {error: 'no #chatElement'};
    const scroll = root.querySelector('div.batch-block-scroll');
    if (!scroll) return {error: 'no .batch-block-scroll'};
    const blocks = [...scroll.children];
    const out = [];
    blocks.forEach((block, i) => {
        const lis = [...block.querySelectorAll('ul > li')];
        out.push({
            blockIndex: i + 1,
            blockText: (block.innerText || '').slice(0, 300),
            items: lis.map(li => ({
                text: (li.innerText || '').trim().slice(0, 200),
                hrefs: [...li.querySelectorAll('a[href]')].map(a => a.href),
            })),
        });
    });
    return {blockCount: blocks.length, blocks: out};
}
"""


def extract_models(batch_url):
    """Abre o batch group e retorna {modelo: run_url(chatId)} em ordem de DOM.

    Reusa uma aba ja carregada na URL do batch quando existe (goto em nova
    aba pode esgotar timeout quando o servidor esta lento pesado), e retenta
    o goto uma vez antes de desistir.
    """
    with sync_playwright() as p, browser_session(p) as ctx:
        pages = [pg for pg in ctx.pages if pg.url.split("#")[0] == batch_url]
        page = pages[0] if pages else ctx.new_page()
        if not pages:
            last_exc = None
            for attempt in range(2):
                try:
                    # "commit" em vez de "domcontentloaded": o app e SPA com
                    # polling e o evento pode atrasar; o wait_for_selector
                    # abaixo cuida do resto.
                    page.goto(batch_url, wait_until="commit", timeout=45_000)
                    last_exc = None
                    break
                except Exception as exc:  # timeout transitório de rede/app
                    last_exc = exc
                    page.wait_for_timeout(5_000)
            if last_exc is not None:
                page.close()
                raise SystemExit(f"goto falhou apos 2 tentativas: {last_exc}")
        try:
            page.wait_for_selector(
                "#chatElement div.batch-block-scroll", timeout=30_000
            )
        except Exception:
            print(
                "WARN: seletor do batch-block-scroll nao apareceu; seguindo",
                file=sys.stderr,
            )
        page.wait_for_timeout(5_000)
        data = page.evaluate(EXTRACT_JS)
        if not pages:
            page.close()
    if data.get("error"):
        raise SystemExit(f"Erro na extracao: {data['error']}")
    models = {}
    for block in data["blocks"]:
        for item in block["items"]:
            model = (item["text"] or "").splitlines()[0].strip()
            chat_url = next(
                (h for h in item["hrefs"] if "chatId=" in h), None
            )
            if model and chat_url:
                models[model] = chat_url
    return data, models


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    data, models = extract_models(url)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n{len(models)} modelo(s) com run URL:", file=sys.stderr)
    for model, run_url in models.items():
        print(f"  {model}: {run_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
