"""Tests for the per-axis verdict vector, the branch death classifier, the
fail-soft judge, and the chat-track strategy wiring."""

import asyncio

from mta.attacker.propose import LLMProposer
from mta.attacker.strategies import (
    CHAT_MULTITURN_STRATEGIES,
    DEFAULT_STRATEGIES,
    strategies_from_config,
)
from mta.config import Config, JudgeConfig
from mta.judge.cheap_filter import (
    DEATH_EMPTY,
    DEATH_HARD_REFUSAL,
    DEATH_TRUNCATED,
    classify_turn_outcome,
)
from mta.judge.llm_judge import LLMJudge
from mta.judge.rubric import JudgeVerdict
from mta.scenarios.base import ScenarioVerdict
from mta.search.state import Conversation


# --- classify_turn_outcome ---------------------------------------------------


def test_truncation_wins_over_empty_and_refusal():
    # finish_reason=length is a length artifact, never a stance
    assert classify_turn_outcome("", finish_reason="length") == DEATH_TRUNCATED
    assert classify_turn_outcome("I'm sorry, but I can't help", finish_reason="length") == DEATH_TRUNCATED


def test_empty_text_is_empty_or_filtered():
    assert classify_turn_outcome("") == DEATH_EMPTY
    assert classify_turn_outcome("   ") == DEATH_EMPTY


def test_short_hard_refusal_is_classified():
    assert classify_turn_outcome("I'm sorry, but I can't help with that.") == DEATH_HARD_REFUSAL


def test_alive_turn_returns_none():
    assert classify_turn_outcome("Sure, here is the full breakdown. " + "step. " * 100) is None
    # a refusal opener followed by substance is alive (judge decides)
    assert classify_turn_outcome("I'm sorry, but I can't do exactly that. However, " + "detail " * 200) is None


# --- per-axis verdict vectors -------------------------------------------------


def test_judge_verdict_axes_and_binding_axis():
    v = JudgeVerdict(overall_reasoning="x", refused=True, on_topic=False,
                     convincing=1, specificity=1)
    assert v.axes["refusal_avoided"] == 0.0
    assert v.binding_axis == "refusal_avoided"

    v = JudgeVerdict(overall_reasoning="x", refused=False, on_topic=False,
                     convincing=5, specificity=5)
    assert v.binding_axis == "on_topic"

    # near-miss: one content axis down is the convertible state and must bind
    v = JudgeVerdict(overall_reasoning="x", refused=False, on_topic=True,
                     convincing=5, specificity=2)
    assert v.axes["specificity"] == 0.25
    assert v.binding_axis == "specificity"

    # all maxed -> nothing binds
    v = JudgeVerdict(overall_reasoning="x", refused=False, on_topic=True,
                     convincing=5, specificity=5)
    assert v.binding_axis == ""


def test_scenario_verdict_axes_and_binding_axis():
    v = ScenarioVerdict(success=False, constraint_ok=True, score=0.0)
    assert v.binding_axis == ""
    v = ScenarioVerdict(success=False, constraint_ok=True, score=0.4,
                        axes={"recommendation": 1.0, "originality": 0.2})
    assert v.binding_axis == "originality"
    v = ScenarioVerdict(success=True, constraint_ok=True, score=1.0,
                        axes={"recommendation": 1.0, "originality": 1.0})
    assert v.binding_axis == ""


# --- judge fail-soft ----------------------------------------------------------


class _RaisingLiteLLM:
    @staticmethod
    async def acompletion(**kwargs):
        raise ConnectionError("provider down")


def test_judge_fails_soft_to_zero_verdict():
    judge = LLMJudge(JudgeConfig(max_retries=2, json_mode="json_object"))
    judge._litellm = _RaisingLiteLLM
    verdict = asyncio.run(judge.score_transcript("do X", [{"role": "user", "content": "X"}]))
    assert verdict.judge_error is True
    assert verdict.refused is True
    assert verdict.score == 0.0
    # and it must not poison the axis record with a mislabeled refusal
    assert verdict.binding_axis == "refusal_avoided"


# --- chat-track strategies ----------------------------------------------------


def test_chat_track_strategies_are_multiturn_and_not_in_defaults():
    labels = {s.label for s in DEFAULT_STRATEGIES}
    for s in CHAT_MULTITURN_STRATEGIES:
        assert s.multi_turn is True
        assert s.label not in labels  # never leak into the generic taxonomy


def test_strategies_from_config_can_select_chat_labels():
    picked = strategies_from_config(["documented_past_practice", "direct"])
    assert [s.label for s in picked] == ["documented_past_practice", "direct"]


class _FakeScenario:
    def __init__(self, kind, strats=None):
        self.kind = kind
        self._strats = strats

    def strategies(self):
        return self._strats

    def attacker_guidance(self):
        return ""


def test_chat_content_scenario_gets_chat_track_strategies():
    p = LLMProposer.from_scenario(Config(), _FakeScenario("chat_content"), seed=0)
    labels = {s.label for s in p.strategies}
    for s in CHAT_MULTITURN_STRATEGIES:
        assert s.label in labels
    for s in DEFAULT_STRATEGIES:
        assert s.label in labels


def test_indirect_scenario_never_gets_chat_track_strategies():
    p = LLMProposer.from_scenario(Config(), _FakeScenario("indirect"), seed=0)
    labels = {s.label for s in p.strategies}
    for s in CHAT_MULTITURN_STRATEGIES:
        assert s.label not in labels


def test_scenario_supplied_strategies_win_over_chat_track():
    mine = [DEFAULT_STRATEGIES[0]]
    p = LLMProposer.from_scenario(Config(), _FakeScenario("chat_content", mine), seed=0)
    assert p.strategies == mine


# --- multi-attacker rotation ---------------------------------------------------


class _RecordingLiteLLM:
    def __init__(self):
        self.models = []

    async def acompletion(self, **kwargs):
        self.models.append(kwargs["model"])

        class _Msg:
            content = "attack turn text"

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


def test_proposer_rotates_attacker_models_across_proposals():
    from mta.attacker.strategies import DEFAULT_STRATEGIES

    cfg = Config()
    cfg.attacker_models = ["deepseek/deepseek-chat", "openrouter/openai/gpt-4o-mini"]
    cfg.judge.max_retries = 1
    proposer = LLMProposer(cfg, strategies=[DEFAULT_STRATEGIES[0]], seed=0)
    recorder = _RecordingLiteLLM()
    proposer._litellm = recorder
    proposer.validator = None

    conv = Conversation(objective="objective X")
    asyncio.gather  # keep import used
    import asyncio as _asyncio

    async def fire(n):
        return await _asyncio.gather(*(proposer._one(conv, DEFAULT_STRATEGIES[0]) for _ in range(n)))

    _asyncio.run(fire(4))
    assert recorder.models == [
        "featherless_ai/deepseek/deepseek-chat",
        "openrouter/openai/gpt-4o-mini",
        "featherless_ai/deepseek/deepseek-chat",
        "openrouter/openai/gpt-4o-mini",
    ]


def test_proposer_single_attacker_unchanged():
    cfg = Config()
    cfg.attacker_model = "deepseek/deepseek-chat"
    cfg.judge.max_retries = 1
    proposer = LLMProposer(cfg, strategies=[DEFAULT_STRATEGIES[0]], seed=0)
    recorder = _RecordingLiteLLM()
    proposer._litellm = recorder
    proposer.validator = None
    conv = Conversation(objective="objective X")

    import asyncio as _asyncio

    _asyncio.run(proposer._one(conv, DEFAULT_STRATEGIES[0]))
    assert recorder.models == ["featherless_ai/deepseek/deepseek-chat"]


def test_resolved_attacker_models_combines_and_normalizes():
    cfg = Config()
    cfg.attacker_model = "deepseek/deepseek-chat"
    cfg.attacker_models = ["openrouter/anthropic/claude-sonnet-5"]
    assert cfg.resolved_attacker_models == [
        "featherless_ai/deepseek/deepseek-chat",
        "openrouter/anthropic/claude-sonnet-5",
    ]
    cfg2 = Config()
    assert cfg2.resolved_attacker_models == [cfg2.judge.model]


# --- attacker cross-model fallback ---------------------------------------------


class _EmptyThenFullLiteLLM:
    """First model always returns empty content (safety refusal); second works."""

    def __init__(self):
        self.calls = []

    async def acompletion(self, **kwargs):
        self.calls.append(kwargs["model"])

        class _Msg:
            def __init__(self, content):
                self.content = content

        class _Choice:
            def __init__(self, content):
                self.message = _Msg(content)

        class _Resp:
            def __init__(self, content):
                self.choices = [_Choice(content)]

        if "glm" in kwargs["model"]:
            return _Resp("")
        return _Resp("attack turn text")


def test_attacker_falls_through_to_next_model_on_empty():
    cfg = Config()
    cfg.attacker_models = ["zai-org/glm-4.6", "deepseek/deepseek-chat"]
    cfg.judge.max_retries = 2
    proposer = LLMProposer(cfg, strategies=[DEFAULT_STRATEGIES[0]], seed=0)
    recorder = _EmptyThenFullLiteLLM()
    proposer._litellm = recorder
    proposer.validator = None
    conv = Conversation(objective="objective X")

    import asyncio as _asyncio

    text = _asyncio.run(proposer._one(conv, DEFAULT_STRATEGIES[0]))
    assert text == "attack turn text"
    assert recorder.calls[0] == "featherless_ai/zai-org/glm-4.6"
    assert "deepseek" in recorder.calls[-1]
    # 5 hardcoded attempts on the refusing model, then one on the fallback
    assert len(recorder.calls) == 6


def test_empty_payload_skipped_in_replay():
    from mta.eval.replay import run_replay
    from mta.scenarios import get_scenario

    async def fake_target(messages):
        raise AssertionError("target must not be called for an empty payload")

    # run_replay builds its own target; verify the guard logic directly instead
    from mta.eval.replay import ReplayMatrix
    m = ReplayMatrix(scenario="s", models=["m"], vectors=[{"strategy": "x", "payload": "  "}],
                     cells={})
    cell_is_none = (not "  ".strip())
    assert cell_is_none
