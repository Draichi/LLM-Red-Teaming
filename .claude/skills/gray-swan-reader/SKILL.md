---
name: gray-swan-reader
description: >-
  Read Gray Swan Arena pages (app.grayswan.ai, login required) with a Playwright
  browser that reuses a saved session: discover the URLs on a listing page, open
  each one, and save the content as local Markdown files for agent reading. Use
  when the operator wants arena/challenge/batch content pulled for writeups,
  calibration, or disposition maps instead of copy-pasting it by hand.
---

# Gray Swan Arena page reader

Self-contained tool in `grayswan-reader/` (Playwright + Chromium, persistent
login profile). It is **read-only**: it never types, clicks, or submits anything
in the arena — guardrail 2 of AGENTS.md (submission stays manual) is unaffected.

Run from the tool folder:

```bash
cd grayswan-reader
.venv/bin/python reader.py <command> ...
```

## Commands

| Command | Purpose |
|---|---|
| `login <url>` | One-time interactive login (visible browser window). See below — the operator runs this. Repeat only when the session expires. |
| `links <listing-url> --match REGEX` | List the URLs found on a page. Discovery step — run this first. |
| `fetch <listing-url> --match REGEX` | Extract the listing's links, open each one, save `pages/<slug>-<hash>.md` + the `pages/manifest.json` index. Already-saved pages are skipped (`--force` refetches). |
| `open <url>` | Save a single page to Markdown. |

Every saved `.md` has frontmatter (`url`, `title`, `fetched_at`, `chars`) plus
the full page text. **Agent reading flow: `pages/manifest.json` first (url →
file, status, char count), then the `.md` files.** A `status` of `vazio` or
`erro` in the manifest means the page needs a refetch.

Useful flags: `--limit N`, `--exclude REGEX`, `--settle S` (extra wait for the
SPA to render, default 2s), `--delay S`, `--headed` (visible browser, debug),
`--content-selector CSS`, `--wait-selector CSS`.

## Login (operator, one-time)

Login is interactive — the agent cannot do it. Ask the operator to run, from
`grayswan-reader/`:

```
! .venv/bin/python reader.py login https://app.grayswan.ai
```

They log in inside the opened window, then press Enter in the terminal; the
session persists in `browser_profile/`. Symptom of an expired session: fetched
pages contain a login / "sign in" screen instead of content → ask the operator
to re-run the command above.

## Gotchas

- `--match` is a **regex**: a literal `?` must be escaped (`challenge\?batch`).
  When discovery returns 0 URLs, suspect the pattern first, then the SPA wait
  (raise `--settle`).
- One command at a time — the browser profile is single-instance ("Browser is
  closed" / profile-lock errors mean another instance is running).
- Empty or partial content on arena pages: raise `--settle`, or target the
  content with `--wait-selector` / `--content-selector`; `--headed` shows what
  the page is actually rendering.

## Guardrails (repo policy)

- `browser_profile/` (login cookies) and `pages/` (real arena content) are
  gitignored — **never version them, never paste their content into tracked
  files** (same policy as `data/`).
- Reading pages is fine; automating submission is not. This tool has no write
  path to the arena by design — keep it that way.
