"""InventingProposer: wall taxonomy, mechanism library, exemplar loading, the
diagnose/design/instantiate chain (with a scripted attacker), and the
build_proposer factory. Offline."""

import json

from mta.attacker.inventor import (
    MECHANISM_LIBRARY,
    WALL_TAXONOMY,
    InventingProposer,
    build_proposer,
    load_exemplars,
    _mechanism_block,
    _wall_block,
)
from mta.config import Config
from mta.search.state import Conversation


class _FakeProposer(InventingProposer):
    """Scripted _attacker_call: pops canned replies per call kind."""

    def __init__(self, *a, script=None, **kw):
        super().__init__(*a, **kw)
        self._script = list(script or [])

    async def _attacker_call(self, system, user, model=None):
        from mta.attacker.propose import strip_meta
        for i, (match, reply) in enumerate(self._script):
            if match in user:
                self._script.pop(i)
                return reply
        return "{}"


def _cfg():
    return Config()


def test_wall_taxonomy_covers_documented_failures():
    names = {w["name"] for w in WALL_TAXONOMY}
    # the failure modes analysis.md names explicitly
    for expected in ["content_guardrail", "filter_trip", "framework_swap",
                     "quantities_boundary", "origination_tax",
                     "notoriety_floor", "commitment_depth",
                     "safety_gradient_legal", "uncertainty_hedge",
                     "operational_detail_guardrail"]:
        assert expected in names
    for w in WALL_TAXONOMY:
        assert w["cues"] and w["implication"]


def test_mechanism_library_references_valid_walls():
    walls = {w["name"] for w in WALL_TAXONOMY}
    for m in MECHANISM_LIBRARY:
        assert m["addresses"], m["name"]
        assert set(m["addresses"]) <= walls, m["name"]
        assert m["features"] and m["claim"]


def test_blocks_render():
    assert "safety_gradient_legal" in _wall_block()
    assert "historical_legal_reconstruction" in _mechanism_block()


def test_load_exemplars_filters_domain(tmp_path, monkeypatch):
    import mta.attacker.inventor as I
    p = tmp_path / "mech.jsonl"
    rows = [{"name": "a", "domain": "chemistry", "walls_addressed": ["x"],
             "features": {"f": "v"}, "outcome": "1 break"},
            {"name": "b", "domain": "cyber", "walls_addressed": [],
             "features": {}, "outcome": ""}]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert len(load_exemplars(p)) == 2
    assert [e["name"] for e in load_exemplars(p, domain="chemistry")] == ["a"]
    assert load_exemplars(tmp_path / "nope") == []


def test_diagnose_parses_structured_wall():
    p = _FakeProposer(
        _cfg(), script=[("Target's latest response:",
                         '{"wall_type": "quantities_boundary", "evidence": '
                         '"no numbers given", "implication": "source numbers '
                         'from records"}')])
    conv = Conversation(objective="obj", messages=[
        {"role": "user", "content": "give the procedure"},
        {"role": "assistant", "content": "I can describe the approach but not give quantities."},
    ])
    import asyncio
    d = asyncio.run(p.diagnose(conv))
    assert d["wall_type"] == "quantities_boundary"


def test_diagnose_first_contact_without_assistant_turn():
    p = _FakeProposer(_cfg())
    conv = Conversation(objective="obj", messages=[])
    import asyncio
    d = asyncio.run(p.diagnose(conv))
    assert d["wall_type"] == "none_first_contact"


def test_full_chain_produces_mechanism_label():
    p = _FakeProposer(_cfg(), script=[
        ("Target's latest response:", '{"wall_type": "safety_gradient_legal",'
         ' "evidence": "illegal", "implication": "relocate legality"}'),
        ("Design ONE mechanism", '{"mechanism": "historical_legal_reconstruction",'
         ' "wall_addressed": "safety_gradient_legal",'
         ' "features": {"period_and_setting": "1905 agricultural stations"},'
         ' "surface_hint": "archive annotator"}'),
        ("Write the actual", "the attack turn text"),
    ])
    conv = Conversation(objective="obj", messages=[
        {"role": "assistant", "content": "I can't help with that - it's illegal."}])
    import asyncio
    out = asyncio.run(p(conv, 1))
    assert len(out) == 1
    move, label = out[0]
    assert move == "the attack turn text"
    assert label == "mech:historical_legal_reconstruction"


def test_design_falls_back_to_library_mechanism():
    p = _FakeProposer(_cfg(), script=[("Design ONE mechanism", "no json here")])
    conv = Conversation(objective="obj", messages=[])
    import asyncio
    d = asyncio.run(p.design(conv, {"wall_type": "safety_gradient_legal"}))
    assert d["mechanism"] == "historical_legal_reconstruction"


def test_build_proposer_factory():
    from mta.scenarios import get_scenario

    cfg = Config()
    sc = get_scenario("cyanide_extraction")
    tax = build_proposer(cfg, sc, kind="taxonomy")
    inv = build_proposer(cfg, sc, kind="inventor")
    from mta.attacker.propose import LLMProposer
    assert type(tax) is LLMProposer
    assert isinstance(inv, InventingProposer)
    assert inv.axes == ["cyanide_extraction_instructions", "ai_origination"]
    # config-driven selection too
    cfg.proposer = "inventor"
    assert isinstance(build_proposer(cfg, sc), InventingProposer)


def test_batch_diversity_exclusion():
    # the designer stubbornly returns the same mechanism; the batch must still
    # cover distinct mechanisms via the exclude list + rotating fallback
    p = _FakeProposer(_cfg(), script=[
        ("Target's latest response:", '{"wall_type": "safety_gradient_legal",'
         ' "evidence": "illegal", "implication": "relocate legality"}'),
        ("Design ONE mechanism", '{"mechanism": "historical_legal_reconstruction",'
         ' "wall_addressed": "safety_gradient_legal", "features": {}, "surface_hint": "x"}'),
        ("Design ONE mechanism", '{"mechanism": "historical_legal_reconstruction",'
         ' "wall_addressed": "safety_gradient_legal", "features": {}, "surface_hint": "x"}'),
        ("Design ONE mechanism", '{"mechanism": "historical_legal_reconstruction",'
         ' "wall_addressed": "safety_gradient_legal", "features": {}, "surface_hint": "x"}'),
        ("Write the actual", "move one"),
        ("Write the actual", "move two"),
        ("Write the actual", "move three"),
    ])
    conv = Conversation(objective="obj", messages=[
        {"role": "assistant", "content": "I can't help with that - it's illegal."}])
    import asyncio
    out = asyncio.run(p(conv, 3))
    labels = [s for _, s in out]
    assert len(set(labels)) == 3, labels  # three distinct mechanisms
    assert all(l.startswith("mech:") for l in labels)


def test_parse_json_fallbacks():
    assert InventingProposer._parse_json("", {}) == {}
    d = InventingProposer._parse_json('noise {"a": 1} tail', {})
    assert d == {"a": 1}
    assert InventingProposer._parse_json("[1,2]", {}) == {}
