"""Phase 6 reporting: the headline table and charts.

Consumes the RunResult lists from the loop / single-turn / human runs and emits
the one table and one chart the whole project exists to produce.
"""

from __future__ import annotations

from pathlib import Path

from mta.eval.run_loop import asr
from mta.search.state import RunResult


def headline_table(
    single: list[RunResult],
    beam: list[RunResult],
    human_summary: dict | None,
    budget_turns: int,
) -> str:
    solved_beam = sum(1 for r in beam if r.solved)
    solved_single = sum(1 for r in single if r.solved)
    rows = [
        "| Method | Objectives solved | Budget | ASR |",
        "|---|---|---|---|",
    ]
    if human_summary:
        n = human_summary["n"]
        rows.append(
            f"| Human (manual) | {round(human_summary['asr'] * n)} / {n} "
            f"| {budget_turns} turns | {human_summary['asr']:.2f} |"
        )
    rows.append(
        f"| Single-turn baseline | {solved_single} / {len(single)} "
        f"| 1 turn | {asr(single):.2f} |"
    )
    rows.append(
        f"| Beam search loop | {solved_beam} / {len(beam)} "
        f"| {budget_turns} turns | {asr(beam):.2f} |"
    )
    return "\n".join(rows)


def asr_chart(
    single: list[RunResult], beam: list[RunResult], out_path: Path
) -> Path | None:
    """Bar chart of ASR@1 vs ASR@budget. Requires the `report` extra."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(["single-turn", "beam search"], [asr(single), asr(beam)])
    ax.set_ylabel("ASR")
    ax.set_ylim(0, 1)
    ax.set_title("Attack success rate at fixed budget")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
