import pytest

from mta.providers import extract_json_object, thinking_off_extra_body


def test_thinking_off_shape():
    assert thinking_off_extra_body() == {"chat_template_kwargs": {"enable_thinking": False}}


def test_extract_plain_json():
    assert extract_json_object('{"refused": true}') == {"refused": True}


def test_extract_passthrough_dict():
    assert extract_json_object({"a": 1}) == {"a": 1}


def test_extract_from_fenced_block():
    text = '```json\n{"refused": false, "convincing": 4}\n```'
    assert extract_json_object(text) == {"refused": False, "convincing": 4}


def test_extract_from_prose_wrapped():
    text = 'Here is my verdict:\n{"refused": false, "specificity": 5}\nHope that helps.'
    assert extract_json_object(text) == {"refused": False, "specificity": 5}


def test_extract_raises_without_object():
    with pytest.raises(ValueError):
        extract_json_object("no json here at all")


def test_normalize_model_routes_openrouter():
    from mta.eval.bench import normalize_model
    # OpenRouter ids (provider/model) pass through untouched
    assert normalize_model("openrouter/anthropic/claude-sonnet-4") == "openrouter/anthropic/claude-sonnet-4"
    assert normalize_model("openrouter/meta-llama/llama-3.3-70b-instruct") == "openrouter/meta-llama/llama-3.3-70b-instruct"
    # existing behavior unchanged: bare ids still default to Featherless, known prefixes pass
    assert normalize_model("Qwen/Qwen2.5-72B-Instruct") == "featherless_ai/Qwen/Qwen2.5-72B-Instruct"
    assert normalize_model("featherless_ai/Qwen/Qwen3-235B-A22B") == "featherless_ai/Qwen/Qwen3-235B-A22B"
    assert normalize_model("anthropic/claude-opus-5") == "anthropic/claude-opus-5"


def test_replay_matrix_renders_failure_reasons_section():
    from mta.eval.replay import ReplayMatrix

    matrix = ReplayMatrix(
        scenario="s", models=["featherless_ai/X/Y"], vectors=[{"strategy": "strat_a", "payload": "p"}],
        cells={(0, "featherless_ai/X/Y"): {"breaks": 0, "trials": 2, "best": 0.2,
                                           "near_misses": 0, "worst_axes": {},
                                           "reasons": ["missing: empty-inbox-claim"]}},
    )
    md = matrix.markdown()
    assert "## Failure reasons (deduped)" in md
    assert "missing: empty-inbox-claim" in md
