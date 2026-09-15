# multiturn-attacker

An automated search loop that discovers multi-turn jailbreaks, benchmarked
against an experienced human red teamer **at an equal turn budget**.

**Thesis.** A judge is only worth building if something optimizes against its
score. Here the judge is a *value function for beam search*, not a reporting
tool — so it is calibrated against human labels before any search consumes it.

## Headline deliverable

| Method | Objectives solved | Budget | ASR |
|---|---|---|---|
| Human (manual) | ? / 20 | 6 turns | ? |
| Single-turn baseline | ? / 50 | 1 turn | ? |
| Beam search loop | ? / 50 | 6 turns | ? |

## Scope (locked)

One target family, one benchmark, one metric — ASR@6turns (budget-normalized so
human vs. machine is a fair comparison). Objectives are sampled from a public
benchmark (JailbreakBench / HarmBench); the judge is calibrated on human-labeled
data. Everything out of scope is in [FUTURE.md](FUTURE.md).

## Install

```bash
uv sync --extra judge --extra api        # judge + API targets/attacker
uv sync --extra local                    # add the local MLX dev target
uv sync --extra report --extra dev       # charts + tests
```

Set provider keys for [litellm](https://docs.litellm.ai/) as usual
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …). Model IDs are litellm-routed
(`anthropic/claude-opus-5`, `gpt-4o`, …).

## Run (phase order — each gate must pass before the next)

```bash
uv run mta fetch-data                            # download the calibration set
uv run mta calibrate --config configs/main.yaml  # Phase 1 GATE: kappa>=0.7, FPR<0.1
uv run mta single    --config configs/main.yaml  # Phase 3 floor: ASR@1turn
uv run mta eval      --config configs/main.yaml  # Phase 4: beam search, ASR@6turns
uv run mta human     --config configs/main.yaml  # Phase 5: human baseline (interactive)
```

`mta calibrate` exits non-zero if the Phase 1 gate fails, and writes
`reports/judge_calibration.md` (confusion matrix + kappa + FPR) either way — a
credible artifact on its own.

## The judge (Phase 1, the part that matters)

The judge never emits a bare success number. It fills a **decomposition** —
`refused`, `on_topic`, `convincing` (1–5), `specificity` (1–5) — via structured
output, and the scalar `score ∈ [0,1]` is derived in code
(`mta/judge/rubric.py`). Forcing the decomposition is what stops the classic
failure of scoring "did not refuse" as "attack succeeded". The rubric wording
and score formula follow **StrongREJECT** (Souly et al., 2024), the instrument
built specifically because naive judges overcount jailbreak success.

Calibration binarizes the judge score at `success_threshold` and compares it
against majority-vote human labels (HarmBench classifier val set) with Cohen's
kappa and a confusion matrix. **The false-positive rate is the metric that
matters most**: a judge that rewards refusals makes the search optimize toward
nothing.

### Calibration result (n = 602, `featherless_ai/Qwen/Qwen3-235B-A22B`)

Accepted **with a documented limitation** — full report in
[`reports/judge_calibration.md`](reports/judge_calibration.md):

| Metric | Value | Target | Status |
|---|---|---|---|
| Cohen's kappa | 0.713 | ≥ 0.7 | met |
| False-positive rate | 0.146 | < 0.1 | not met |
| Recall | 0.861 | — | — |

The kappa bar is met; the strict FPR < 0.1 bar is not, and no threshold clears
both at once (where kappa ≥ 0.7, FPR ≈ 0.15). This is the known LLM-judge ceiling
— StrongREJECT-class judges sit at kappa ~0.70–0.75 and don't reach FPR < 0.1
against binary harm labels. The residual false positives are a specific class:
**plausible-but-non-functional / fabricated** content (a broken code snippet,
fabricated names) that reads as specific but isn't usable, which the judge can't
verify. Getting here took a rubric that judges against the *canonical* objective
(not the obfuscated prompt), treats disclaimer-then-deliver as success, and uses
few-shot near-miss examples. We operate at threshold 0.25 and, because the human
baseline and the loop are scored by the **same** judge, the consistent bias
largely cancels in the head-to-head. `mta report` regenerates this offline.

## Phase 2 — two-tier cheap gate (validated)

Before the concurrency-1 big judge, two cheap tiers screen out refusals:
**tier 1** a free regex, **tier 2** a small ungated model
(`Qwen/Qwen2.5-7B-Instruct`, runs 4-parallel). Validated against the human
labels with `mta gate-eval` — the metric that matters is **blinding** (a real
jailbreak wrongly screened, hiding it from the judge and the search):

| Gate | Blinding rate | Judge-call reduction |
|---|---|---|
| regex only | 0.000 | 0.09 |
| regex + classifier (naïve) | 0.31 | 0.36 |
| regex + classifier + length guard | **0.010** | **0.165** |

Two design findings made it safe: (1) frame the small model as neutral
**refusal detection**, never "does this help accomplish [harmful goal]" — the
latter trips its own safety training and it screens out 60% of real jailbreaks;
(2) a **length guard** — only short replies can be a clean refusal, so long
replies (including disclaimer-then-deliver jailbreaks) bypass the gate straight
to the judge. The 0.165 reduction is a conservative floor: the calibration set
is enriched with hard positives, so a real search (where the target refuses far
more) saves much more. `gate.max_filter_chars` trades reduction against blinding.

## Human-baseline validity

Run `mta human` on its sampled objectives **before** looking at any automated
results for those objectives. Contamination destroys the entire claim. The human
CLI logs every turn with timestamps and scores the final transcript with the
same judge, and records wall-clock per objective (the time column is the
commercial argument).

## Responsible disclosure

This repo ships the **search machinery and the strategy taxonomy — never a
payload library.** No working attack strings against frontier models live here;
the attacker instantiates high-level strategy *labels* at run time. The
`data/behaviors/objectives.jsonl` file is a placeholder — populate it from the
public benchmark yourself.

The held-out transfer target (Gray Swan arena) is **manual submission only**, by
their rules. There is deliberately no browser automation or scripted submission
in this repo. If a strategy transfers to a production model, report it to that
vendor before writing about it. Methodology, aggregate numbers, and the harness
are publishable; working payloads are not.
