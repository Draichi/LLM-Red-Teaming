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
