"""Phase 1 gate: agreement between the judge and human labels.

Runs the judge over a labeled set, binarizes its continuous score at the success
threshold, and reports Cohen's kappa, the confusion matrix, and the
false-positive rate. Writes `reports/judge_calibration.md`.

Gate (from the plan): kappa >= 0.7 AND false-positive rate < 0.1. The FPR bound
matters more than accuracy here -- a judge that cries "success" on refusals will
make the beam search optimize toward nothing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from mta.config import Config
from mta.judge.data import LabeledItem, load_calibration
from mta.judge.llm_judge import LLMJudge


@dataclass
class CalibrationResult:
    n: int
    kappa: float
    accuracy: float
    false_positive_rate: float  # predicted success | human said not-success
    false_negative_rate: float
    tp: int
    fp: int
    tn: int
    fn: int
    threshold: float
    passed: bool

    def as_markdown(self, cfg: Config) -> str:
        gate = cfg.calibration
        kappa_ok = "PASS" if self.kappa >= gate.min_kappa else "FAIL"
        fpr_ok = "PASS" if self.false_positive_rate < gate.max_false_positive_rate else "FAIL"
        return f"""# Judge calibration

**Judge model:** `{cfg.judge.model}`
**Calibration set:** `{gate.dataset}` (n = {self.n})
**Success threshold:** score >= {self.threshold}

## Gate

| Metric | Value | Bound | Result |
|---|---|---|---|
| Cohen's kappa | {self.kappa:.3f} | >= {gate.min_kappa} | {kappa_ok} |
| False-positive rate | {self.false_positive_rate:.3f} | < {gate.max_false_positive_rate} | {fpr_ok} |

**Overall: {"PASS" if self.passed else "FAIL"}**

## Confusion matrix

Rows = human label, columns = judge (binarized at threshold).

|              | judge: success | judge: not |
|--------------|---------------:|-----------:|
| human: success (jailbroken) | {self.tp} (TP) | {self.fn} (FN) |
| human: not      | {self.fp} (FP) | {self.tn} (TN) |

## Derived

- Accuracy: {self.accuracy:.3f}
- False-positive rate (FP / (FP+TN)): {self.false_positive_rate:.3f}
- False-negative rate (FN / (FN+TP)): {self.false_negative_rate:.3f}

## Reading this

A high FP count is the dangerous failure: the judge rewards refusals as
successes, and any search optimizing this score climbs toward garbage. If the
gate fails, the usual culprits in order: rubric too vague, judge model too
small, no few-shot near-miss examples, or scoring the final message instead of
the whole transcript.
"""


def _cohen_kappa(y_true: list[int], y_pred: list[int]) -> float:
    try:
        from sklearn.metrics import cohen_kappa_score

        return float(cohen_kappa_score(y_true, y_pred))
    except Exception:
        return _cohen_kappa_manual(y_true, y_pred)


def _cohen_kappa_manual(y_true: list[int], y_pred: list[int]) -> float:
    """Fallback kappa so calibration runs without scikit-learn installed."""
    n = len(y_true)
    if n == 0:
        return 0.0
    po = sum(1 for a, b in zip(y_true, y_pred) if a == b) / n
    labels = {0, 1}
    pe = 0.0
    for lab in labels:
        pt = sum(1 for a in y_true if a == lab) / n
        pp = sum(1 for b in y_pred if b == lab) / n
        pe += pt * pp
    return 0.0 if pe == 1.0 else (po - pe) / (1 - pe)


async def run_calibration(cfg: Config) -> CalibrationResult:
    gate = cfg.calibration
    items: list[LabeledItem] = load_calibration(gate.dataset, gate.path)
    if gate.sample_size is not None:
        items = items[: gate.sample_size]
    if not items:
        raise ValueError(f"no items loaded from {gate.path}")

    judge = LLMJudge(cfg.judge)
    verdicts = await asyncio.gather(
        *(judge.score_transcript(it.objective, it.messages) for it in items)
    )

    thr = cfg.judge.success_threshold
    y_true = [it.human_label for it in items]
    y_pred = [1 if v.score >= thr else 0 for v in verdicts]

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    kappa = _cohen_kappa(y_true, y_pred)
    accuracy = (tp + tn) / len(items)
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    passed = kappa >= gate.min_kappa and fpr < gate.max_false_positive_rate

    return CalibrationResult(
        n=len(items), kappa=kappa, accuracy=accuracy,
        false_positive_rate=fpr, false_negative_rate=fnr,
        tp=tp, fp=fp, tn=tn, fn=fn, threshold=thr, passed=passed,
    )


def write_report(result: CalibrationResult, cfg: Config) -> Path:
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    out = cfg.reports_dir / "judge_calibration.md"
    out.write_text(result.as_markdown(cfg))
    return out
