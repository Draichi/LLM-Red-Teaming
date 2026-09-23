"""learn-writeups parser: kill-log PASS rows mapped to vector prompts. Offline."""

from pathlib import Path

from mta.attacker.ingest import parse_writeup

_WRITEUP = """# Demo Scenario

## Objective

Demo.

## Vector 1 - Historical frame

Frame prose here.

```
PROMPT-ONE-TEXT
```

## INTEL Round 1

Obsidian Eel delivered partially.

## Vector 2 - Fiction frame

```
PROMPT-TWO-TEXT
```

## Kill log

| Model | Best vector | Verdict | Judge score / notes |
|---|---|---|---|
| Silver Ant Magical | Vector 1 | COMPLIED / judge PASS | Full pass after follow-up |
| Obsidian Eel Enormous | Vector 2 | JUDGE FAIL | 80/80/10 |
| Wood Zebra Supreme | Vector 2 | JUDGE FAIL / hard refusal | 40/30/10 |
"""


def test_parse_writeup_maps_pass_rows_to_vectors(tmp_path):
    f = tmp_path / "demo_scenario.md"
    f.write_text(_WRITEUP)
    vecs = parse_writeup(f)
    # only Vector 1 has a PASS row -> only it is a product
    assert len(vecs) == 1
    v = vecs[0]
    assert v.scenario == "demo_scenario"
    assert v.vector_id == "V1"
    assert "Historical frame" in v.title
    assert "PROMPT-ONE-TEXT" in v.prompt
    assert len(v.passes) == 1 and "Silver Ant Magical" in v.passes[0]


def test_parse_writeup_no_pass_no_products(tmp_path):
    f = tmp_path / "all_fail.md"
    f.write_text(_WRITEUP.replace("COMPLIED / judge PASS", "JUDGE FAIL"))
    assert parse_writeup(f) == []


def test_parse_writeup_missing_fence_skips_vector(tmp_path):
    f = tmp_path / "no_fence.md"
    f.write_text(_WRITEUP.replace("```\nPROMPT-ONE-TEXT\n```", "no fenced prompt"))
    vecs = parse_writeup(f)
    assert all("PROMPT-ONE-TEXT" not in v.prompt for v in vecs)
