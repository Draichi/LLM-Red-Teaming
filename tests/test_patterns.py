"""Community pattern corpus: parsing, trust labels, and the design-prompt
block. Offline."""

import json

from mta.attacker.patterns import (
    PATTERNS_PATH,
    TRUST_LABEL,
    load_patterns,
    parse_pattern_file,
    patterns_block,
)


def test_parse_file_with_headers(tmp_path):
    f = tmp_path / "VENDOR.mkd"
    f.write_text("intro line\n\n## Alpha pattern\n\nDo the alpha thing with "
                 "enough body text to count as a pattern, yes indeed it is.\n\n"
                 "## Beta\n\nBeta body, also long enough to be a real pattern "
                 "for the parser to keep and ingest later on.\n")
    pats = parse_pattern_file(f)
    assert [p["name"] for p in pats] == ["VENDOR:Alpha pattern", "VENDOR:Beta"]
    assert "alpha thing" in pats[0]["prompt"]


def test_parse_file_without_headers_is_one_pattern(tmp_path):
    f = tmp_path / "RAW.mkd"
    f.write_text("No headers here, just a long raw jailbreak body " * 6)
    pats = parse_pattern_file(f)
    assert len(pats) == 1 and pats[0]["name"] == "RAW"


def test_parse_skips_tiny_bodies(tmp_path):
    f = tmp_path / "TINY.mkd"
    f.write_text("short")
    assert parse_pattern_file(f) == []


def test_load_and_block_with_trust_label(tmp_path, monkeypatch):
    import mta.attacker.patterns as P
    rows = [{"name": "token_smuggling_variant", "claim": "tries X",
             "features": {"encoding": "special tokens"},
             "trust": TRUST_LABEL, "source": "l1b3rt4s:CHATGPT:x"}]
    p = tmp_path / "patterns.jsonl"
    p.write_text(json.dumps(rows[0]) + "\n")
    monkeypatch.setattr(P, "PATTERNS_PATH", p)
    assert len(load_patterns()) == 1
    block = patterns_block()
    assert "UNVALIDATED" in block and "token_smuggling_variant" in block


def test_block_empty_when_no_store(tmp_path, monkeypatch):
    import mta.attacker.patterns as P
    monkeypatch.setattr(P, "PATTERNS_PATH", tmp_path / "nope.jsonl")
    assert "no community patterns" in patterns_block()
