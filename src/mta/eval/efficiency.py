"""Aggregate run-cost records into reports/efficiency.md (SOTA item 6).

Every run command appends one JSON line to data/runs/costs.jsonl (see
cli._log_cost): {ts, cmd, scenario, target, solved, wall_clock_s,
attacker_calls, target_calls, judge_calls, queries_to_first_break,
usd_estimate}. This module folds those records into per-scenario cost-per-break
numbers. Pure Python: unit-tested offline, no API.
"""

from __future__ import annotations

import json
from pathlib import Path

COSTS_FILENAME = "costs.jsonl"


def load_costs(runs_dir: Path) -> list[dict]:
    path = runs_dir / COSTS_FILENAME
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _fold(rows: list[dict]) -> dict:
    """Sum a group of run records into the aggregate row."""
    solved = sum(1 for r in rows if r.get("solved"))
    calls = sum(r.get("target_calls", 0) + r.get("attacker_calls", 0)
                + r.get("judge_calls", 0) for r in rows)
    usd = [r["usd_estimate"] for r in rows if r.get("usd_estimate") is not None]
    qfb = [r["queries_to_first_break"] for r in rows
           if r.get("queries_to_first_break") is not None]
    return {
        "runs": len(rows),
        "solved": solved,
        "calls": calls,
        "target": sum(r.get("target_calls", 0) for r in rows),
        "attacker": sum(r.get("attacker_calls", 0) for r in rows),
        "judge": sum(r.get("judge_calls", 0) for r in rows),
        "usd": sum(usd) if usd else None,
        "qfb": (sum(qfb) / len(qfb)) if qfb else None,
        "wall": sum(r.get("wall_clock_s", 0.0) for r in rows),
    }


def _row(label: str, c: dict) -> str:
    cpb = f"{c['calls'] / c['solved']:.1f}" if c["solved"] else "—"
    usd = f"{c['usd']:.4f}" if c["usd"] is not None else "—"
    qfb = f"{c['qfb']:.1f}" if c["qfb"] is not None else "—"
    return (f"| {label} | {c['runs']} | {c['solved']} | {c['target']} | {c['attacker']} "
            f"| {c['judge']} | {cpb} | {usd} | {qfb} | {c['wall']:.1f} |")


def efficiency_markdown(rows: list[dict]) -> str:
    if not rows:
        return ("# Efficiency\n\nNo run records yet. Every run command appends one "
                "line to `data/runs/costs.jsonl`; once runs have happened this "
                "report shows cost per break and queries-to-first-break.\n")
    lines = [
        "# Efficiency",
        "",
        f"{len(rows)} run record(s) from `data/runs/costs.jsonl`. Cost per break = "
        "total calls / solved runs. `USD` needs a `prices` table in the config "
        "(per-model USD per call); without it only calls are counted.",
        "",
        "| Scenario | Runs | Solved | Target calls | Attacker calls | Judge calls "
        "| Cost/break (calls) | USD total | Mean queries-to-first-break | Wall clock (s) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r.get("scenario", "?"), []).append(r)
    for scen in sorted(by):
        lines.append(_row(scen, _fold(by[scen])))
    lines.append(_row("**TOTAL**", _fold(rows)))
    return "\n".join(lines) + "\n"


def write_efficiency_report(runs_dir: Path, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / "efficiency.md"
    out.write_text(efficiency_markdown(load_costs(runs_dir)))
    return out
