# MTA Roadmap

Living plan — where the project is, where it's going, what's left. Update as we
go. (Supersedes the original `FUTURE.md`, which described a since-abandoned scope.)

## Mission

An elite red-teaming harness that **discovers and validates transferable
jailbreak vectors** for the Gray Swan arena. Develop locally against a proxy →
rank by reliability + transfer → submit the strong ones to the (manual) arena →
refine against real arena feedback.

## Where we are (2026-09-17)

**Working end-to-end.** Modular scenario plugins (verifiable vs fuzzy judges),
beam search + single-shot injection, separate attacker model, reliability testing,
transfer matrices, vector library, arena-feedback refine loop, proxy calibration.

**Best result so far:** `malware_game` (indirect injection) — a `dormant_trigger`
vector developed on Mistral-Medium, reliable on 5/6 local models, **broke 3/13
live arena models** (two at 100/90), up from 1/13 for the first hand attempt.

**Also proven:** `hotel_booking` — beam auto-rediscovered a human's manual break.

**Scenarios:** `malware_game`, `hotel_booking`, `secret_extraction`,
`ransomware_injection` (verifiable); `radical_propaganda` (fuzzy, human-verified).

**Key lessons banked:**
- Verifiable judges (~0 FPR) >> fuzzy rubric for trustworthy automation.
- The attacker model matters as much as the target; a coherent mainstream
  instruction-follower (DeepSeek-V3.1) beats an abliterated one for injection
  scenarios (abliterated only helps for overtly-harmful content generation).
- Reliability testing (`--trials`) is essential — single "solves" are noisy.
- Not every (scenario × model) is breakable (GLM-4.7 resisted every malware vector).
- Develop-on-proxy-then-transfer works; the proxy must resemble arena models
  (Western, non-Chinese suspected; Mistral > Qwen locally).

## Now / next

- [ ] **Push local commits to `origin`** (several ahead: proxy-eval, README, etc.).
- [ ] **Run `proxy-eval`** on malware_game truth → confirm Mistral > Qwen with a number.
- [ ] **Lift malware_game 3/13 → higher.** Two arena near-misses (ruby tiger,
      shadow flamingo) failed only on Originality (<70). Refine for more
      independent paraphrase / technical detail; re-submit.
- [ ] **Western-proxy ensemble** dev: mine on Mistral, filter with
      `replay-vectors --models "Mistral,phi-4"` to keep vectors that break both.

## Provider migration (planned, next weeks)

- [ ] **Move off Featherless → OpenRouter.** Reasons: Featherless is $25/mo + per
      token, and most Western proxies (Llama, Gemma, GPT, Claude, Gemini) are
      gated/absent — the exact models that best resemble the arena.
- [ ] OpenRouter covers both roles: frontier **targets** + DeepSeek **attacker**
      (the winning attacker), so no Featherless hybrid needed (except maybe an
      uncensored attacker for `radical_propaganda`).
- [ ] Harness change is small: add `openrouter/` routing in `normalize_model` +
      the openai-compat route for tool calls; wire the API key.
- [ ] Validate the switch with `proxy-eval`: are OpenRouter frontier models
      better arena proxies than Mistral?

## Backlog / ideas

- [ ] `proxy-eval` for non-indirect scenarios (agentic/content), not just single-shot.
- [ ] More Gray Swan scenario plugins as they come up (image/multimodal is the
      big untouched type — needs a multimodal target).
- [ ] Auto-refine-on-arena-failure convenience (feed an arena response file →
      variants), tightening the manual loop.
- [ ] Stealth/obfuscation helper: emit the payload already wrapped in real
      background-colour BBCode / zero-width unicode for direct arena paste.
- [ ] A per-scenario "difficulty" report: which models are walls vs soft.

## Guardrails (do not drift)

- The arena stays **manual** — no scripted submission, ever.
- The repo ships **machinery + abstract strategies, never payloads**; discovered
  vectors, transcripts, arena responses live in gitignored `data/`.
- A "solved" from a **fuzzy** judge is a human-review candidate, not a verified break.
- Don't force a false positive on an unbreakable target — report the wall.
