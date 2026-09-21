"""Item 6 efficiency report: folds data/runs/costs.jsonl records into
cost-per-break per scenario. Pure Python, offline."""

import json

from mta.eval.efficiency import efficiency_markdown, write_efficiency_report


def _row(scenario, solved, target=10, attacker=4, judge=2, qfb=None, usd=None,
         wall=30.0):
    return {"ts": "2026-09-21T00:00:00", "cmd": "agentic_beam", "scenario": scenario,
            "target": "m", "solved": solved, "wall_clock_s": wall,
            "attacker_calls": attacker, "target_calls": target, "judge_calls": judge,
            "queries_to_first_break": qfb, "usd_estimate": usd}


def test_efficiency_markdown_cost_per_break():
    rows = [_row("hotel_booking", True, qfb=6, usd=0.5),
            _row("hotel_booking", True, qfb=10, usd=0.7),
            _row("ransomware_injection", False)]
    md = efficiency_markdown(rows)
    assert "hotel_booking" in md and "ransomware_injection" in md
    # hotel: (10+4+2) calls x 2 solved runs = 16.0 calls per break
    assert "16.0" in md
    # mean queries-to-first-break = (6+10)/2 = 8.0
    assert "8.0" in md
    # unsolved scenario reports its zeros, not a fake cost per break
    assert "| ransomware_injection | 1 | 0 |" in md
    assert "**TOTAL**" in md


def test_efficiency_markdown_empty():
    assert "No run records yet" in efficiency_markdown([])


def test_write_efficiency_report(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "costs.jsonl").write_text(json.dumps(_row("s", True, usd=0.1)) + "\n")
    out = write_efficiency_report(runs, tmp_path / "reports")
    assert out.exists()
    assert "s" in out.read_text()
