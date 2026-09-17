from math import isclose

from mta.eval.proxy_eval import ProxyResult, spearman


def test_spearman_perfect():
    assert isclose(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)


def test_spearman_inverse():
    assert isclose(spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)


def test_spearman_constant_is_zero():
    assert spearman([1, 1, 1], [1, 2, 3]) == 0.0


def test_spearman_monotone_not_linear():
    # ranks match even though values aren't linearly related
    assert isclose(spearman([1, 2, 3, 4], [1, 4, 9, 16]), 1.0)


def test_ranked_and_markdown():
    r = ProxyResult(
        scenario="malware_game",
        payload_names=["dormant", "v1", "v_best"],
        arena_rates=[0.23, 0.08, 0.0],
        local_rates={
            "org/GoodProxy": [1.0, 0.4, 0.0],   # tracks arena order -> high corr
            "org/BadProxy": [0.0, 0.5, 1.0],    # inverted -> negative corr
        },
    )
    ranked = r.ranked()
    assert ranked[0][0] == "org/GoodProxy" and ranked[0][1] > 0.9
    assert ranked[-1][0] == "org/BadProxy" and ranked[-1][1] < 0
    md = r.markdown()
    assert "Best proxy: `GoodProxy`" in md and "arena (truth)" in md
