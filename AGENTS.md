# AGENTS.md

Operating notes for AI agents working in this repo. Read `README.md` for what MTA
is and `ROADMAP.md` for where it's going; this file is the how-to-work-here.

## What this is

A red-teaming harness that discovers/validates transferable jailbreak vectors for
the Gray Swan arena. Scenario-agnostic core (`src/mta/{attacker,search,eval}`) +
per-scenario `(target, judge)` plugins (`src/mta/scenarios/`).

## Build & test

- `uv run pytest -q` — full suite; must be green before any commit.
- Tests are **offline** (no network/API). Keep them that way: judge/constraint
  logic is pure Python and unit-tested; anything hitting a model is exercised
  only via the live CLI, never in tests.
- Run the tool: `uv run mta <command> ...` (see the README command table).

## Non-negotiable guardrails

1. **No payloads *versioned*** (they exist locally, just never committed). The
   repo's tracked files ship machinery + abstract strategy *labels*, never working
   attack strings. Discovered vectors, run transcripts, arena responses, and
   calibration data are real files you use, kept under `data/` and **gitignored**
   (`data/vectors/`, `data/runs/`, `data/calibration/*`) — present on disk, absent
   from git. Before every commit, verify no `data/`/`*.txt`/key is staged.
2. **The arena stays manual.** Never script or automate arena submission.
3. **A "solved" from a fuzzy judge needs human confirmation.** Scenarios have two
   judge kinds: *verifiable* (tool-misuse, injection — success is a checkable fact,
   ~0 FPR, a "solved" is a real break you trust) and *fuzzy* (content generation
   like `radical_propaganda` — an LLM rubric with ~15% false positives; it has
   scored non-harmful text as a break). So a fuzzy "solved" is a **candidate a
   human must read the transcript to confirm**, never an auto-accepted break.
4. **Don't force a false positive.** If a target resists, report the wall
   (see GLM-4.7). The verifiable judge must never claim a break that didn't happen.
5. **Commit/push only when the user explicitly asks.** Do the work, run tests,
   leave the tree dirty. Attribution line: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Model conventions (durable)

These survive the provider migration:

- **Prompted tool-calling** for agentic targets (tools described in the system
  prompt, JSON parsed from the reply) — model-agnostic, works on any provider.
- **Thinking: on for the target** (natural behaviour under attack), **off for the
  attacker** (so it emits the attack, not its planning).
- **Attacker model:** a coherent mainstream instruction-follower (DeepSeek-V3.1)
  beats an abliterated one for injection/tool-misuse; abliterated only helps for
  overtly-harmful content generation. Set with `--attacker-model`.
- **Runs fail soft:** one bad model/attacker call returns an empty result, never
  crashes a long multi-model/multi-turn run.

## Provider plumbing (Featherless today — TRANSIENT, changes with OpenRouter)

Migration to OpenRouter is planned (see `ROADMAP.md`); most of this disappears then.

- Auth via `FEATHERLESS_AI_API_KEY`. Bare `org/model` ids route to Featherless
  (`mta.eval.bench.normalize_model`); `anthropic/…` passes through. Adding
  OpenRouter = a new prefix branch here + its key.
- litellm's `featherless_ai/` provider **rejects `response_format` and `tools`**,
  so today JSON output passes `allowed_openai_params=["response_format"]` and tool
  calls use the OpenAI-compat route (`mta.providers.openai_compat_route`). These
  are Featherless-provider workarounds — OpenRouter supports both natively, so
  revisit `openai_compat_route` and the `allowed_openai_params` calls on migration.
- `chat_template_kwargs.enable_thinking=false` is a Featherless/vLLM kwarg that
  corrupts non-reasoning models; only send it to reasoning models. Provider-specific.

## Code conventions

- Match the surrounding style; scenarios mirror `ransomware_injection.py` /
  `malware_game.py` (indirect) or `hotel_booking.py` (agentic).
- A scenario is a class with `kind` (`indirect` | `agentic` | `chat_content`),
  `system_prompt`, `tools`, `attacker_objective`, `strategies`, `attacker_guidance`,
  a verifiable `judge`/`judge_injection`, and (optional) `validate_payload`,
  `feedback`. Register it in `scenarios/__init__.py`.
- Attacks are graded with a scalar in [0,1] so search has a gradient; keep the
  judge honest (a security-warning or content-leak must NOT score as a break).
- **Score every arena axis.** The arena counts a scenario broken only if EACH of
  its axes is ≥70%. A scenario's judge must score the primary axis *and its
  secondary axes*, and local "solved" must require all of them — else the local
  judge reports breaks the arena rejects on a secondary axis. **Originality has
  been in every scenario** (own words, not parroted → `constraints.origination_score`).
  Identify the axes from the arena spec when scaffolding a new scenario.

## Workflow (the pipeline)

`agentic --runs` (mine) → `replay-vectors --trials` (reliability + transfer) →
`pick-vector` (extract) → arena (manual) → `refine-manual` (harden on real feedback).
`proxy-eval` measures which local model best predicts the arena.
