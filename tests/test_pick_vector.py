from mta.cli import _vector_turns


def test_multi_turn_vector():
    assert _vector_turns({"turns": ["a", "b", "c"]}) == ["a", "b", "c"]


def test_single_shot_payload():
    assert _vector_turns({"payload": "inject"}) == ["inject"]


def test_refine_variant():
    assert _vector_turns({"variant": "attack"}) == ["attack"]


def test_empty_entry():
    assert _vector_turns({"scenario": "x"}) == []
