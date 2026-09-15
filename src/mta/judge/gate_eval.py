"""Validate the Phase 2 classifier gate against human-labeled calibration data.

The one error that matters is BLINDING: the gate screening out a real jailbreak
(human_label = 1) so it never reaches the judge and the search gets no credit.
We also report how many judge calls the gate saves (its whole purpose).

Runs the free regex tier and the classifier tier over the same labeled items and
reports both, so their marginal contributions are visible.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from mta.config import Config
from mta.judge.cheap_filter import is_obvious_refusal
from mta.judge.classifier_gate import LLMClassifierGate
from mta.judge.data import load_calibration


@dataclass
class GateEvalResult:
    n: int
    positives: int          # human_label == 1 (real jailbreaks)
    negatives: int
    # regex tier
    regex_filtered: int
    regex_blinded: int      # positives the regex wrongly dropped
    # regex + classifier
    combined_filtered: int
    combined_blinded: int
    # of negatives, how many correctly screened (judge calls saved)
    negatives_saved: int

    @property
    def blinding_rate(self) -> float:
        return self.combined_blinded / self.positives if self.positives else 0.0

    @property
    def judge_call_reduction(self) -> float:
        return self.combined_filtered / self.n if self.n else 0.0

    def as_text(self, cfg: Config) -> str:
        return (
            f"Gate eval (gate model = {cfg.gate.model})\n"
            f"  items: {self.n}  (positives={self.positives}, negatives={self.negatives})\n"
            f"  regex tier:     filtered {self.regex_filtered:>4}  blinded {self.regex_blinded}\n"
            f"  + classifier:   filtered {self.combined_filtered:>4}  blinded {self.combined_blinded}\n"
            f"  BLINDING RATE (real jailbreaks wrongly screened): "
            f"{self.blinding_rate:.3f}  ({self.combined_blinded}/{self.positives})\n"
            f"  judge-call reduction: {self.judge_call_reduction:.3f}  "
            f"({self.combined_filtered}/{self.n} never reach the judge)\n"
            f"  of {self.negatives} true negatives, {self.negatives_saved} correctly screened"
        )


async def run_gate_eval(cfg: Config, sample_size: int | None = None) -> GateEvalResult:
    items = load_calibration(cfg.calibration.dataset, cfg.calibration.path)
    if sample_size is not None:
        import random

        random.Random(cfg.seed).shuffle(items)
        items = items[:sample_size]

    gate = LLMClassifierGate(cfg.gate)

    def reply_of(it):
        return it.messages[1]["content"] if len(it.messages) > 1 else ""

    regex_flags = [is_obvious_refusal(reply_of(it)) for it in items]
    # classifier only runs on regex survivors (that's how the pipeline works)
    survivor_idx = [i for i, f in enumerate(regex_flags) if not f]
    clf_flags = await asyncio.gather(
        *(gate.is_refusal(items[i].objective, reply_of(items[i])) for i in survivor_idx)
    )
    clf_by_idx = dict(zip(survivor_idx, clf_flags))

    combined = [regex_flags[i] or clf_by_idx.get(i, False) for i in range(len(items))]

    pos = [i for i, it in enumerate(items) if it.human_label == 1]
    neg = [i for i, it in enumerate(items) if it.human_label == 0]

    return GateEvalResult(
        n=len(items),
        positives=len(pos),
        negatives=len(neg),
        regex_filtered=sum(regex_flags),
        regex_blinded=sum(1 for i in pos if regex_flags[i]),
        combined_filtered=sum(combined),
        combined_blinded=sum(1 for i in pos if combined[i]),
        negatives_saved=sum(1 for i in neg if combined[i]),
    )
