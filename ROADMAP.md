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
- Develop-on-proxy-then-transfer works; the proxy must resemble arena models.
  Which proxy is best is **still open** — proxy-eval at n=4 was inconclusive, and
  the "Western > Chinese" hunch is unconfirmed. Use an ensemble until the arena-
  truth file is large enough to measure it.

## Now / next

- [ ] **Push local commits to `origin`** (several ahead: proxy-eval, README, etc.).
- [x] **`proxy-eval` on malware_game (n=4): inconclusive — n too small.** With 4
      payloads (2 tied at 0.0), Spearman is noise; all proxies ranked "high"
      (Qwen +1.0, Mistral +0.94, phi-4 +0.78) with no real separation. Do NOT
      draw a proxy conclusion from this. proxy-eval only becomes useful once the
      arena-truth file has ~10-15 payloads spanning the difficulty range — and
      that truth only accrues as a **byproduct** of normal arena submissions
      (never run arena campaigns just to feed it). The "Mistral > Qwen" hunch is
      unconfirmed; the "Chinese models aren't arena proxies" claim is unsupported.
- [ ] **Proxy choice by ensemble, not by a small-n winner.** Develop against
      Mistral + Qwen-72B (both break, different families); keep vectors that break
      both. Revisit proxy-eval when the truth file is big enough.
- [ ] **Lift malware_game 3/13 → higher.** Two arena near-misses (ruby tiger,
      shadow flamingo) failed only on Originality (<70). Refine for more
      independent paraphrase / technical detail; re-submit.

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

## Per-scenario writeups

Each scenario keeps an engagement writeup at `data/writeups/<scenario>.md`
(gitignored — holds payloads), started at scaffold time from the skill's
`writeup_template.md` and updated every round: scenario + arena axes, intel log,
kill log (model × vector × per-axis scores), the vectors, and reusable lessons.
`malware_game.md` is the first one. It's the memory of what breaks what.

## Guardrails (do not drift)

- The arena stays **manual** — no scripted submission, ever.
- Ship machinery + abstract strategies; **never *version* payloads** — discovered
  vectors, transcripts, arena responses exist locally but live in gitignored
  `data/`, never committed.
- A "solved" from a **fuzzy** judge is a human-review candidate, not a verified break.
- Don't force a false positive on an unbreakable target — report the wall.
