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

**2026-09-18 additions (hazard_hunt arena lessons):** per-axis verdict vectors with
`binding_axis` on both judge types (the scalar hides the convertible near-miss);
branch death classification (`empty_or_filtered` / `truncated` / `hard_refusal` /
`soft_refusal`) recorded on every dropped branch; fail-soft judge (a broken judge
call now scores the branch 0 instead of crashing the run); four chat-track
multi-turn strategies wired into chat_content scenarios only; refine prompts
translate feedback into requirements, never content to copy.

**2026-09-18 chat track, first arena-shaped scenario:** `dll_injection` plugin
(arena's seven technical axes + AI Origination, verbatim from the arena spec) with
a per-axis `AxisJudge` (every axis ≥ 70% floor = the arena's own pass rule, used
by all content runners when a scenario declares `content_judge`) and the
criterion-sliced ladder mode (`run_content_sliced`, `mta agentic --sliced`):
fixed turn skeleton - descriptive opener, one axis cluster per slice gated at the
floor, consolidation last - so the search climbs the same structure that
converted the manual event's hardest near-misses. UNCALIBRATED until a sliced
vector transfers to the live arena.

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

## Provider migration (DONE 2026-09-20, live validation pending a key)

- [x] **OpenRouter routing.** `openrouter/<provider>/<model>` ids pass through
      `normalize_model`; `OPENROUTER_API_KEY` wired via `.env` (litellm reads it
      natively). Featherless stays the default for bare ids (existing configs
      unchanged). Docs + tests updated (100 passing).
- [ ] **Live validation once an OpenRouter key exists:** smoke one target call
      (`mta sweep-models --scenario hotel_booking --models
      "openrouter/meta-llama/llama-3.3-70b-instruct" --attacks 2`), then run
      `proxy-eval` as arena-truth accrues. Until then, treat OpenRouter transfer
      numbers as unmeasured.
- [ ] OpenRouter covers frontier targets + the DeepSeek attacker; keep Featherless
      for the cheap Qwen judge/gate (unit economics: the 235B judge per call).

## Backlog / ideas

- [ ] `proxy-eval` for non-indirect scenarios (agentic/content), not just single-shot.
- [ ] More Gray Swan scenario plugins as they come up (image/multimodal is the
      big untouched type — needs a multimodal target).
- [ ] Auto-refine-on-arena-failure convenience (feed an arena response file →
      variants), tightening the manual loop.
- [ ] Stealth/obfuscation helper: emit the payload already wrapped in real
      background-colour BBCode / zero-width unicode for direct arena paste.
- [ ] A per-scenario "difficulty" report: which models are walls vs soft.

### From the 2026-09 hazard_hunt arena review (mechanisms, not plumbing)

- [ ] **Truncation is its own verdict, not a low score.** Detected now
      (`death: truncated` via finish_reason), but the repair is policy: refire
      the identical vector once before redesigning, then add an output-discipline
      clause (compact code, no docstrings, explanation sacrificable). Arena
      measurement: a truncation "failure" was sampling noise twice.
- [ ] **Beam budget waste:** `beam_search` spends attacker calls on proposals the
      target-call budget will never fire (`budget.take()` breaks only the inner
      loop). Cheap fix; matters on long sweeps.
- [ ] **Mechanism queue against content-class walls** (the two walls that close
      every 18/20 scenario are class-bound, not frame-bound): Bad Likert Judge
      (T1 validated in the arena: both wall models engaged and endorsed the
      rubric; T2 untested at event close), Echo Chamber (anchor on the model's
      own validator text), detector-training-data generation (the artifact IS the
      deliverable). Encode as chat-track strategies once one transfers.
- [ ] **PAIR-style attacker-LLM loop** over the existing judge plumbing (the
      judge_simulator from the sister repo is the offline screen). Biggest
      investment, only worth it after the mechanism queue is measured.

### Chat-track caveat (calibration honesty)

The four `CHAT_MULTITURN_STRATEGIES` are proven in the direct-chat arena
(hazard_hunt), where every scenario is a conversation. MTA's only calibrated,
arena-transferred success is the **indirect** track. Until a chat_content vector
discovered here transfers to the arena, treat chat-track "solved" as
double-unverified: fuzzy judge AND uncalibrated track.

- [ ] **Calibrate the AxisJudge.** The StrongREJECT rubric earned kappa 0.71 on
      HarmBench; the per-axis judge has no such measurement yet. Build
      `data/calibration/arena_truth_dll_injection.jsonl` as a byproduct of arena
      submissions (never as a campaign goal itself) and measure per-axis
      agreement against the arena's real per-axis scores once n is big enough.
- [ ] **More chat plugins once the first transfers:** ldap_injection and
      anti_forensic_self_delete have fully mapped arena axes and documented wall
      models - the stress test for the sliced ladder.

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
