from pathlib import Path

import pytest

from mta.search.budget import Budget
from mta.judge.data import load_harmbench_val

CALIB = Path("data/calibration/harmbench_val.json")


def test_budget_caps_target_calls():
    b = Budget(max_target_calls=3)
    assert b.take() and b.take() and b.take()
    assert not b.take()
    assert b.exhausted
    assert b.summary()["target_calls"] == 3


def test_budget_component_accounting():
    b = Budget(max_target_calls=10)
    b.record_attacker_call()
    b.record_judge_call()
    b.record_judge_call()
    s = b.summary()
    assert s["attacker_calls"] == 1 and s["judge_calls"] == 2


@pytest.mark.skipif(not CALIB.exists(), reason="calibration data not fetched")
def test_harmbench_loader_shape():
    items = load_harmbench_val(CALIB)
    assert len(items) > 100
    it = items[0]
    assert it.human_label in (0, 1)
    assert it.messages[0]["role"] == "user"
    assert it.messages[1]["role"] == "assistant"
    assert it.objective
