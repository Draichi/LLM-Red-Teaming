#!/usr/bin/env python3
"""Intake completo de um batch group da Arena: URLs + transcripts por modelo.

Pipeline (somente leitura; submissao continua 100% manual):

  1. Abre a URL do batch group, extrai (modelo, run URL) de cada bloco de run
     e grava/atualiza o `URLS.md` no diretorio de saida (so a coluna Run URL;
     verdicts e notes existentes sao preservados).
  2. Para cada modelo, abre a run com o reader (--expand restrito) e salva o
     transcript como `<Modelo>.txt` no mesmo diretorio, no mesmo formato dos
     arquivos de run ja usados no workspace (frontmatter + corpo + conteudo
     colapsado). Arquivos ja existentes e nao vazios sao pulados (use
     --force para rebaixar).

Uso:

    .venv/bin/python batch_intake.py "<url-do-batch-group>" <dir-saida> [--force]

Exemplo (wb3s1 v3):

    .venv/bin/python batch_intake.py \
        "https://app.grayswan.ai/arena/challenge/ipi-black-2026?batchGroupId=c72b62d99d487578130e34c085390a8c" \
        ../data/runs/arena/ipi_black/wb3s1/v3
"""

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright
from reader import browser_session, fetch_one
from extract_batch_group_urls import extract_models

TABLE_HEADER = "| Model | Official verdict | Run URL | Notes |"
TABLE_DIVIDER = "|---|---|---|---|"


def update_urls_md(path, models):
    """Cria ou atualiza a coluna Run URL do URLS.md, preservando o restante."""
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        seen = set()
        for i, line in enumerate(lines):
            m = re.match(r"^\|\s*([^|]+?)\s*\|", line)
            if not m or line.startswith("| Model ") or line.startswith("|---"):
                continue
            model = m.group(1)
            if model in models:
                parts = line.split("|")
                # ['', ' model ', ' verdict ', ' url ', ' notes ', '']
                while len(parts) < 5:
                    parts.append("")
                parts[3] = f" {models[model]} "
                lines[i] = "|".join(parts)
                seen.add(model)
        missing = [m for m in models if m not in seen]
        if missing:
            for model in missing:
                lines.append(f"| {model} | pending | {models[model]} | |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        lines = [
            "# Run URLs — batch group intake",
            "",
            "Paste each run URL directly below. The agent reads this file before requesting anything.",
            "",
            TABLE_HEADER,
            TABLE_DIVIDER,
        ]
        lines += [f"| {m} | pending | {u} | |" for m, u in models.items()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def transcript_path(out_dir, model):
    return out_dir / f"{model}.txt"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("batch_url", help="URL do batch group na Arena")
    ap.add_argument("out_dir", help="diretorio de saida (ex.: data/runs/.../v3)")
    ap.add_argument("--force", action="store_true", help="rebaixa runs ja salvas")
    ap.add_argument("--urls-only", action="store_true", help="so passo 1 (URLS.md)")
    ap.add_argument("--limit", type=int, help="baixa no maximo N runs nesta execucao")
    ap.add_argument("--settle", type=float, default=3.0,
                    help="espera por pagina de run, em s (default: 3)")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="pausa entre runs, em s (default: 1)")
    ap.add_argument("--no-output-expand", action="store_true",
                    help="nao expande 'show full output' de tools (economia de "
                         "tokens: outputs >15k chars ficam colapsados no transcript)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/2] Extraindo run URLs de {args.batch_url}")
    _, models = extract_models(args.batch_url)
    if not models:
        raise SystemExit("Nenhum modelo com run URL encontrado no batch group.")
    print(f"      {len(models)} modelo(s) encontrado(s).")

    # Guarda contra bloco stale: se os chatIds extraidos ja existem no
    # URLS.md de uma rodada anterior (mesmo batch group, bloco antigo ainda
    # montado — aconteceu no v8 em 2026-11-03), o batch novo provavelmente
    # ainda nao foi lancado. Aborta antes de gravar/baixar nada.
    new_ids = {u.split("chatId=")[1] for u in models.values() if "chatId=" in u}
    stale_hits = []
    for other in sorted(out_dir.parent.glob("v*/URLS.md")):
        if other == out_dir / "URLS.md":
            continue
        old = set(re.findall(r"chatId=([a-f0-9]+)", other.read_text(encoding="utf-8")))
        overlap = new_ids & old
        if overlap:
            stale_hits.append(f"{other.parent.name}: {len(overlap)} chatId(s) repetidos")
    if stale_hits:
        raise SystemExit(
            "ABORTADO: chatIds extraidos ja constam em rodadas anteriores — o "
            "bloco montado provavelmente e da rodada anterior e o batch novo "
            "ainda nao foi lancado (ou a pagina nao atualizou).\n  "
            + "\n  ".join(stale_hits)
            + "\nConfira no Arena se o novo batch esta lancado e a pagina o "
              "mostra, entao rode de novo."
        )

    urls_md = out_dir / "URLS.md"
    update_urls_md(urls_md, models)
    print(f"      URLS.md atualizado: {urls_md}")

    if args.urls_only:
        return

    pending = [
        (m, u)
        for m, u in models.items()
        if args.force or not transcript_path(out_dir, m).exists()
        or transcript_path(out_dir, m).stat().st_size == 0
    ]
    if args.limit:
        pending = pending[: args.limit]
    print(f"[2/2] Baixando {len(pending)} transcript(s); "
          f"{len(models) - len(pending)} ja existente(s)/pulado(s).")

    failures = []
    with sync_playwright() as p, browser_session(p) as ctx:
        for i, (model, run_url) in enumerate(pending, 1):
            dest = transcript_path(out_dir, model)
            try:
                fpath, chars = fetch_one(
                    ctx, run_url, out_dir, settle=args.settle, expand=True,
                    expand_outputs=not args.no_output_expand,
                )
                fpath.rename(dest)
                print(f"  [{i}/{len(pending)}] {model}: {chars} chars -> {dest.name}")
            except Exception as exc:
                failures.append((model, run_url, str(exc)))
                print(f"  [{i}/{len(pending)}] ERRO {model}: {exc}", file=sys.stderr)
            if args.delay and i < len(pending):
                time.sleep(args.delay)

    ok = len(pending) - len(failures)
    print(f"\nPronto: {ok}/{len(pending)} ok; {len(failures)} falha(s).")
    for model, run_url, err in failures:
        print(f"  FALHA {model}: {run_url} — {err}")


if __name__ == "__main__":
    main()
