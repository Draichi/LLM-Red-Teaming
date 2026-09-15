import asyncio

from mta.config import GateConfig
from mta.judge.classifier_gate import LLMClassifierGate
from mta.judge.gate_eval import GateEvalResult


def test_empty_reply_is_refusal_without_api():
    # empty/whitespace replies are screened without any model call
    gate = LLMClassifierGate.__new__(LLMClassifierGate)  # skip __init__/litellm
    gate.cfg = GateConfig()
    gate.budget = None
    assert asyncio.run(gate.is_refusal("obj", "")) is True
    assert asyncio.run(gate.is_refusal("obj", "   ")) is True


def test_gate_eval_metrics():
    r = GateEvalResult(
        n=100, positives=40, negatives=60,
        regex_filtered=20, regex_blinded=0,
        combined_filtered=35, combined_blinded=1,
        negatives_saved=34,
    )
    assert r.blinding_rate == 1 / 40
    assert r.judge_call_reduction == 35 / 100


def test_blinding_rate_zero_positives():
    r = GateEvalResult(0, 0, 0, 0, 0, 0, 0, 0)
    assert r.blinding_rate == 0.0
    assert r.judge_call_reduction == 0.0
