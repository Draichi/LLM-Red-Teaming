import json

from mta.eval.replay import ReplayMatrix, load_vectors
from mta.scenarios.base import ScenarioVerdict


def _v(solved, score):
    return ScenarioVerdict(success=solved, constraint_ok=True, score=score,
                           reason="", detail={})


def test_transfer_matrix_markdown():
    vectors = [{"strategy": "delimiter_escape", "payload": "p0"},
               {"strategy": "fake_system_channel", "payload": "p1"}]
    models = ["featherless_ai/org/A", "featherless_ai/org/B"]
    cells = {
        (0, "featherless_ai/org/A"): _v(True, 1.0),
        (0, "featherless_ai/org/B"): _v(False, 0.4),
        (1, "featherless_ai/org/A"): _v(True, 1.0),
        (1, "featherless_ai/org/B"): _v(True, 1.0),
    }
    md = ReplayMatrix("ransomware_injection", models, vectors, cells).markdown()
    assert "Transfer matrix" in md
    assert "delimiter_escape" in md and "fake_system_channel" in md
    # vector 0 transfers to 1/2, vector 1 to 2/2
    assert "1/2 |" in md and "2/2 |" in md
    # per-model summary present
    assert "A 2/2" in md and "B 1/2" in md


def test_load_vectors_dedup_and_limit(tmp_path, monkeypatch):
    import mta.eval.replay as R
    d = tmp_path / "vectors"
    d.mkdir()
    f = d / "ransomware_injection.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in [
        {"payload": "a", "strategy": "s1"},
        {"payload": "b", "strategy": "s2"},
        {"payload": "a", "strategy": "s1"},  # dup
    ]))
    monkeypatch.setattr(R, "VECTORS_DIR", d)
    vecs = load_vectors("ransomware_injection")
    assert len(vecs) == 2                       # deduped
    assert vecs[0]["payload"] == "a"            # newest-first (last line was 'a')
    assert len(load_vectors("ransomware_injection", limit=1)) == 1


def test_load_vectors_missing_file(tmp_path, monkeypatch):
    import mta.eval.replay as R
    monkeypatch.setattr(R, "VECTORS_DIR", tmp_path / "nope")
    assert load_vectors("ransomware_injection") == []
