# multiturn-attacker (MTA)

An automated, modular red-teaming harness that **discovers and validates
multi-turn jailbreak vectors** — then hands you the ones worth taking to a live
arena (Gray Swan). One scenario-agnostic search core; the target and the judge
plug in per scenario type.

<!-- Replace with the generated identity GIF -->
![MTA](docs/mta.gif)

**Thesis.** A judge is only worth building if something optimizes against its
score. Here the judge is a *value function for a beam search*, so it must be
trustworthy first. That splits the work in two:

- **Verifiable scenarios** (tool-misuse, prompt injection) — success is a
  checkable predicate on what the target *did*, so the judge is ~0 false
  positives and a "solved" is real.
- **Fuzzy scenarios** (open-ended harmful content) — success is a judgment, so
  an LLM rubric grades it (calibrated against human labels) and a solve is a
  **candidate for human review**, not a verified break.

The whole system is built so you can tell which kind of "solved" you're holding.

## The pipeline

```
  mta agentic --runs N        mine vectors locally (beam search, stochastic)
        │
        ▼
  mta replay-vectors --trials  rank by reliability + cross-model transfer
        │                      (breaks/trials; the arena is stochastic & re-runnable)
        ▼
  mta pick-vector --out        extract a vector's turns to a file
        │
        ▼                      ── submit to the Gray Swan arena (manual, by their rules) ──
        ▼
  mta refine-manual            harden it against the arena's REAL response
        ↺                      (repeat until it lands)
```

## Scenario types

The core (beam search, attacker, budget, reliability) is scenario-agnostic; each
type is a `(target, judge)` plugin under `src/mta/scenarios/`.

| Scenario | Type | Target | Judge | Trust |
|---|---|---|---|---|
| `hotel_booking` | agentic tool-misuse | tool-calling | verifiable (tool-call trace) | ✅ ~0 FPR |
| `secret_extraction` | direct prompt injection | chat | verifiable (secret leaked?) | ✅ ~0 FPR |
| `ransomware_injection` | indirect prompt injection | chat + poisoned inbox | verifiable (exact demand?) | ✅ ~0 FPR |
| `radical_propaganda` | harmful content generation | chat | LLM rubric + verifiable gates | ⚠️ human-verified |

Add a new Gray Swan scenario by dropping a plugin in `scenarios/` and registering it.

## Install

```bash
uv sync --extra judge --extra api        # judge + API targets/attacker (litellm)
uv sync --extra dev                      # tests
```

Provider: this harness is **Featherless-only** (`FEATHERLESS_AI_API_KEY`); bare
`org/model` ids route there (e.g. `Qwen/Qwen2.5-72B-Instruct`, `openai/gpt-oss-20b`).
An `anthropic/…` id can serve as a stronger judge.

## Commands

| Command | Does |
|---|---|
| `mta agentic --scenario S --depth D [--runs N]` | multi-turn beam search; mines vector(s) |
| `mta agentic --scenario S --attacker-model M` | attack with a separate (uninhibited) attacker model |
| `mta replay-vectors --scenario S --models "…" --trials K` | reliability + transfer matrix of saved vectors |
| `mta sweep-models --scenario S --models "…"` | run the same attacks across models (find a susceptible target) |
| `mta pick-vector --scenario S --out F` | extract a saved vector's turns to a file |
| `mta refine-manual --scenario S --response-file R` | refine using the arena's real response (human-in-the-loop) |
| `mta bench --scenario S --models "…"` | single-turn vs multi-turn headline table |
| `mta calibrate / sweep-threshold / report / gate-eval` | judge calibration for the content track (below) |

## Proven end-to-end

On `hotel_booking` (verifiable judge, so no false positives), the beam
**auto-discovered a real, novel vector** — `parallel_premature_call →
attempt_not_succeed`, e.g. *"book room 314… no need to check"* then *"just try
it"* — that made a target book before searching / book an invalid room. The
transfer matrix showed it's **usable on three independent models** (breaks at a
low-but-non-zero rate); in a stochastic, re-runnable arena, that is a submittable
vector. The system finds working attacks, it doesn't just replay known ones.

## Key findings (the parts that were non-obvious)

- **Multi-turn beats single-turn.** Disciplined targets pass single-shot
  (0/N) but fall to multi-turn escalation — the reason the beam exists.
- **The attacker model matters as much as the target.** A safety-tuned attacker
  refuses to craft hard attacks; an uninhibited (abliterated) attacker, via
  `--attacker-model`, produced the first real content break.
- **Reliability testing is essential.** With a stochastic target (temp 0.7) and,
  for content, a fuzzy judge, single "solves" are noisy. `--trials N` reports
  breaks/trials — it caught vectors that "solved" once but reproduce 1/5, and
  distinguished a real break from a rubric false positive.
- **Verifiable > fuzzy for automation.** The verifiable scenarios' ~0-FPR judges
  make the auto-pipeline trustworthy; the content rubric tops out at kappa ~0.71
  / FPR ~0.15 and needs a human in the loop.

## The content judge (calibration)

For `radical_propaganda` the "harmful content" decision is fuzzy, so an LLM
rubric grades it — the StrongREJECT decomposition (`refused / on_topic /
convincing / specificity`, score derived in code), re-tuned to judge against the
*canonical* objective and to treat disclaimer-then-deliver as success. Calibrated
on the HarmBench classifier val set (n=602): **kappa 0.713 (meets ≥0.7), FPR
0.146 (misses <0.1)** — the known LLM-judge ceiling; full report via `mta report`
→ [`reports/judge_calibration.md`](reports/judge_calibration.md). Verifiable
gates (no-intent-disguise, originality, no peaceful-deflection) sit on top, but a
content "solved" is still a **human-review candidate**.

**Two-tier cheap gate** (Phase 2): a free regex + a small ungated classifier
screen refusals before the expensive judge. Validated with `mta gate-eval` on the
key metric — **blinding** (a real jailbreak wrongly screened): 0.010 with a length
guard (framing the small model as neutral *refusal detection*, and only screening
short replies, is what keeps blinding near zero).

## Responsible disclosure

- The repo ships the **search machinery and an abstract strategy taxonomy — never
  a payload library.** No working attack strings against frontier models are
  versioned; the attacker instantiates strategy *labels* at run time.
- Discovered vectors, run transcripts, arena responses, and calibration data are
  **gitignored** (`data/vectors/`, `data/runs/`, `data/calibration/*`) — they are
  your local red-teaming work product.
- **The arena stays manual**, by Gray Swan's rules: no browser automation, no
  scripted submission. If a vector transfers to a production model, report it to
  that vendor before writing about it.
