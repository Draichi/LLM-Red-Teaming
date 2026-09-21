"""Item 6 statistics: Wilson intervals, sequential-trial escalation, the
promotion gate, and the RunCost dollar estimate. Pure Python, offline."""

from mta.stats import (
    arena_eligible,
    escalation_batches,
    fmt_reliability,
    reliability_decided,
    usd_estimate,
    wilson_interval,
)


def test_wilson_edges():
    assert wilson_interval(0, 0) == (0.0, 1.0)
    lo, hi = wilson_interval(0, 5)
    assert lo == 0.0 and 0.40 < hi < 0.45
    lo, hi = wilson_interval(5, 5)
    assert 0.55 < lo < 0.58 and hi == 1.0


def test_wilson_brackets_the_fraction():
    for s in range(0, 21):
        lo, hi = wilson_interval(s, 20)
        assert 0.0 <= lo <= s / 20 <= hi <= 1.0


def test_wilson_narrows_with_n():
    _, hi_small = wilson_interval(1, 2)
    _, hi_big = wilson_interval(5, 10)
    assert hi_big < hi_small


def test_reliability_decided():
    assert reliability_decided(5, 5, 0.5)      # lower bound cleared threshold
    assert reliability_decided(0, 5, 0.5)      # upper bound fell below it
    assert not reliability_decided(2, 5, 0.5)  # 2/5 still straddles
    assert not reliability_decided(0, 0, 0.5)


def test_arena_eligible_uses_lower_bound():
    # 4/5 = 0.8 point estimate, but the lower bound is ~0.38 -> NOT eligible.
    # This is the whole point of the promotion gate: no interval, no promotion.
    assert not arena_eligible(4, 5, 0.5)
    assert arena_eligible(15, 20, 0.5)
    assert not arena_eligible(0, 0, 0.5)


def test_escalation_batches():
    assert escalation_batches(5, 20) == [5, 10, 5]
    assert escalation_batches(5, 5) == [5]
    assert escalation_batches(1, 20) == [1, 10, 9]
    assert escalation_batches(0, 20) == []


def test_fmt_reliability():
    assert fmt_reliability(3, 5).startswith("3/5 [")
    assert fmt_reliability(0, 0) == "0/0 [--]"


def test_usd_estimate():
    prices = {"featherless_ai/org/T": 0.01, "featherless_ai/org/J": 0.02,
              "featherless_ai/org/A1": 0.005, "featherless_ai/org/A2": 0.015}
    summary = {"target_calls": 10, "attacker_calls": 4, "judge_calls": 10}
    usd = usd_estimate(summary, prices, target_model="featherless_ai/org/T",
                       attacker_models=["featherless_ai/org/A1", "featherless_ai/org/A2"],
                       judge_model="featherless_ai/org/J")
    assert usd == round(10 * 0.01 + 4 * 0.01 + 10 * 0.02, 4)  # attacker = avg(A1, A2)
    assert usd_estimate(summary, {}, target_model="T", attacker_models=[],
                        judge_model="J") is None
    # known prices for none of the models used -> None, not a fake zero
    assert usd_estimate(summary, {"X": 1.0}, target_model="T", attacker_models=[],
                        judge_model="J") is None
