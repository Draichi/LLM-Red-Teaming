import json

from mta.eval.replay import ReplayMatrix, load_vectors


def _c(breaks, trials):
    return {"breaks": breaks, "trials": trials, "best": 1.0}


def test_transfer_matrix_markdown():
    vectors = [{"strategy": "delimiter_escape", "payload": "p0"},
               {"strategy": "fake_system_channel", "payload": "p1"}]
    models = ["featherless_ai/org/A", "featherless_ai/org/B"]
    cells = {
        (0, "featherless_ai/org/A"): _c(3, 3),   # reliable
        (0, "featherless_ai/org/B"): _c(0, 3),   # never
        (1, "featherless_ai/org/A"): _c(3, 3),   # reliable
        (1, "featherless_ai/org/B"): _c(2, 3),   # reliable (>=50%)
    }
    md = ReplayMatrix("ransomware_injection", models, vectors, cells).markdown()
    assert "Transfer matrix" in md
    assert "delimiter_escape" in md and "fake_system_channel" in md
    assert "3/3" in md and "2/3" in md and "0/3" in md
    # vector 0 reliable on 1/2 models, vector 1 on 2/2
    assert "| 1/2 |" in md and "| 2/2 |" in md
    # per-model reliability summary present
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
