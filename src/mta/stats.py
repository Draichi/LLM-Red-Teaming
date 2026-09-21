"""Statistics and efficiency helpers (SOTA_implementation.md item 6).

Small-n reliability is reported as a Wilson score interval, not a raw fraction:
`--trials 5` cannot separate 3/5 from 5/5, and the promote-to-arena decision
rests on the interval's lower bound, not the point estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Z_DEFAULT = 1.96  # 95% confidence
# Sequential-trials escalation (the plan's rule): run 5; if the Wilson interval
# still straddles the promotion threshold, run 10 more; stop at 20.
ESCALATION_STEP = 10


def wilson_interval(successes: int, trials: int, z: float = Z_DEFAULT) -> tuple[float, float]:
    """Wilson score interval. Correct at small n, unlike the normal approximation."""
    if trials <= 0:
        return (0.0, 1.0)
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return (max(0.0, center - half), min(1.0, center + half))


def fmt_reliability(breaks: int, trials: int) -> str:
    """`3/5 [0.23-0.88]` -- the breaks/trials fraction plus its Wilson bounds."""
    if trials <= 0:
        return "0/0 [--]"
    lo, hi = wilson_interval(breaks, trials)
    return f"{breaks}/{trials} [{lo:.2f}-{hi:.2f}]"


def reliability_decided(breaks: int, trials: int, threshold: float) -> bool:
    """True once the interval no longer straddles the threshold: either the lower
    bound cleared it (eligible) or the upper bound fell below it (dead)."""
    if trials <= 0:
        return False
    lo, hi = wilson_interval(breaks, trials)
    return lo >= threshold or hi <= threshold


def arena_eligible(breaks: int, trials: int, threshold: float) -> bool:
    """Promotion gate (item 6): arena-eligible only when the Wilson LOWER bound
    clears the threshold -- a point estimate above it is not enough."""
    return trials > 0 and wilson_interval(breaks, trials)[0] >= threshold


def escalation_batches(initial: int, max_trials: int, step: int = ESCALATION_STEP) -> list[int]:
    """Batch sizes for sequential trials, e.g. (5, 20) -> [5, 10, 5].
    Budget is spent only where the answer is still in doubt."""
    if initial <= 0 or max_trials <= 0:
        return []
    batches = [min(initial, max_trials)]
    total = batches[-1]
    while total < max_trials:
        b = min(step, max_trials - total)
        batches.append(b)
        total += b
    return batches


@dataclass
class RunCost:
    """Efficiency counters attached to every run record (data/runs/costs.jsonl)."""

    attacker_calls: int
    target_calls: int
    judge_calls: int
    queries_to_first_break: int | None  # target calls before the first judged break
    wall_clock_s: float
    usd_estimate: float | None          # None when no price is known for any model


def usd_estimate(
    summary: dict,
    prices: dict[str, float],
    *,
    target_model: str,
    attacker_models: list[str],
    judge_model: str,
) -> float | None:
    """Dollar cost of one run from a Budget.summary() dict and a per-model
    USD-per-call table. Missing models cost 0; None when no price is known at all
    (call the table `prices` in the config, keyed by normalized model id)."""
    if not prices:
        return None

    def _avg(models: list[str]) -> float:
        vals = [prices[m] for m in models if m in prices]
        return sum(vals) / len(vals) if vals else 0.0

    known = (
        target_model in prices
        or judge_model in prices
        or any(m in prices for m in attacker_models)
    )
    if not known:
        return None
    total = (
        summary.get("target_calls", 0) * prices.get(target_model, 0.0)
        + summary.get("attacker_calls", 0) * _avg(attacker_models)
        + summary.get("judge_calls", 0) * prices.get(judge_model, 0.0)
    )
    return round(total, 4)
