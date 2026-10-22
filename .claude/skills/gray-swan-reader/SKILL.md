---
name: gray-swan-reader
description: >-
  Read Gray Swan Arena pages (app.grayswan.ai) through the OPERATOR'S OWN
  logged-in Arc browser (CDP attach on port 9222): discover the URLs on a
  listing page, open each one, and save the content as local Markdown files
  for agent reading. Use when the operator wants arena/challenge/chat content
  pulled for writeups, calibration, or disposition maps instead of copy-pasting
  it by hand.
---

# Gray Swan Arena page reader

Self-contained tool in `grayswan-reader/` (Playwright attaching to the
operator's Arc). It is read-only by default; its single sanctioned interaction
is the `--expand` disclosure click below (operator-authorized 2026-10-22).
Guardrail 2 of AGENTS.md (submission stays manual) is unaffected.

**HARD RULE (operator directive, 2026-10-22): the agent NEVER submits a break,
under no circumstances.** The job is reading only: the target model's output,
which tools were called, and with which arguments. The operator pastes the chat
URLs directly — open exactly those URLs; do NOT navigate the batch/run listings
to find runs yourself. Never click SUBMIT or any submission control, never add
any click/submit behavior beyond the sanctioned `--expand` path, and never
drive the operator's browser tabs yourself outside this tool.

Run from the tool folder:

```bash
cd grayswan-reader
.venv/bin/python reader.py <command> ...
```

## Prerequisite (operator, once per Arc session)

The reader attaches to the operator's running Arc via debug port — no login,
no embedded browser, no profile. If connection fails
("Nao consegui conectar em 127.0.0.1:9222"), ask the operator to relaunch:

```
! osascript -e 'quit app "Arc"'; open -na Arc --args --remote-debugging-port=9222
```

If a fetched page shows a "sign in" screen instead of content, the ARC's
session expired: the operator logs in on Arc normally (not in the tool) and
the command is rerun.

## Commands

| Command | Purpose |
|---|---|
| `links <listing-url> --match REGEX` | List the URLs found on a page. Discovery step — run this first. |
| `fetch <listing-url> --match REGEX` | Extract the listing's links, open each one, save `pages/<slug>-<hash>.md` + the `pages/manifest.json` index. Already-saved pages are skipped (`--force` refetches). |
| `open <url>` | Save a single page to Markdown. Chat pages: add `--capture-api --expand` (see below). |

Every saved `.md` has frontmatter (`url`, `title`, `fetched_at`, `chars`) plus
the full page text. **Agent reading flow: `pages/manifest.json` first (url →
file, status, char count), then the `.md` files.** A `status` of `vazio` or
`erro` in the manifest means the page needs a refetch.

Useful flags: `--limit N`, `--exclude REGEX`, `--settle S` (extra wait for the
SPA to render, default 2s), `--delay S`, `--content-selector CSS`,
`--wait-selector CSS`, `--cdp-port N` (default 9222).

## Reading CHAT pages (the operator sends the URLs)

`open <chat-url> --capture-api --expand` saves: the model's full output, the
complete injection payload package, the scenario spec + success criteria (all
in the md's "Conteudo oculto/colapsado" section), the tool-call names and
arguments (rendered only by the `--expand` click), plus `pages/api/*.json`
(SPA responses, complementary).

Tool-call names/arguments render only on "Expand to see details" (client-side
v-if — not in DOM, SSR payload, or XHRs; the app ignores synthetic
`el.click()`). The operator AUTHORIZED (2026-10-22) one restricted interaction
for exactly this: `--expand` clicks ONLY disclosure controls whose text matches
`expand|show more|ver mais|detalhes` and fails
`/submit|break|send|post|reply|delete|confirm|place|order|pay|refund/i` — via
real browser input on the element itself, 1 click each, max 30. This is
already the tool's only click path; do not add or request any other
interaction, and never touch submit-adjacent controls.

## Gotchas

- `--match` is a **regex**: a literal `?` must be escaped (`challenge\?batch`).
  When discovery returns 0 URLs, suspect the pattern first, then the SPA wait
  (raise `--settle`).
- One command at a time.
- Tabs open visibly in the operator's Arc (the price of using the real
  browser) and are closed at the end; the tool only disconnects when done —
  the browser itself stays open.
- Empty or partial content on arena pages: raise `--settle`, or target the
  content with `--wait-selector` / `--content-selector`; the visible tab shows
  what the page is actually rendering.

## Guardrails (repo policy)

- `pages/` (real arena content) is gitignored — **never version it, never
  paste its content into tracked files** (same policy as `data/`).
- Reading pages is fine; automating submission is not. This tool has no write
  path to the arena by design — keep it that way.
