"""Phase 5: the human baseline CLI.

Presents one objective at a time, lets the red teamer type each turn against the
same target under the same fixed turn budget, logs every turn with timestamps,
and scores the final transcript with the SAME judge the loop uses. Records
wall-clock per objective -- the time column is the commercial argument.

Validity protocol (enforced by convention, stated loudly here and in the README):
run the human on its sampled objectives BEFORE looking at any automated results
for those objectives. Contamination destroys the entire claim.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from mta.config import Config
from mta.judge.llm_judge import LLMJudge
from mta.targets.base import build_target


async def run_human_session(cfg: Config, objectives: list[str], out_path: Path) -> None:
    target = build_target(cfg.target)
    judge = LLMJudge(cfg.judge)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fh = out_path.open("a")
    try:
        for i, obj in enumerate(objectives, 1):
            print(f"\n=== Objective {i}/{len(objectives)} ===\n{obj}\n")
            print(f"Budget: {cfg.search.depth} turns. Type your turn, or /skip.\n")
            messages: list[dict] = []
            started = time.time()
            for turn in range(cfg.search.depth):
                user = input(f"[turn {turn + 1}] you> ").strip()
                if user in ("/skip", "/next"):
                    break
                messages.append({"role": "user", "content": user})
                reply = await target(messages)
                messages.append({"role": "assistant", "content": reply})
                print(f"\ntarget> {reply}\n")
            elapsed = time.time() - started
            verdict = (
                await judge.score_transcript(obj, messages) if messages else None
            )
            record = {
                "objective": obj,
                "seconds": round(elapsed, 1),
                "turns_used": sum(1 for m in messages if m["role"] == "user"),
                "score": verdict.score if verdict else 0.0,
                "solved": bool(verdict and verdict.score >= cfg.judge.success_threshold),
                "verdict": verdict.model_dump() if verdict else None,
                "transcript": messages,
            }
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            print(
                f"-> score {record['score']:.2f}, "
                f"{'SOLVED' if record['solved'] else 'not solved'}, "
                f"{record['seconds']}s"
            )
    finally:
        fh.close()


def summarize_human(path: Path) -> dict:
    """Median turns-to-success and median minutes/objective, plus ASR."""
    import statistics as st

    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    if not rows:
        return {}
    solved = [r for r in rows if r["solved"]]
    return {
        "n": len(rows),
        "asr": len(solved) / len(rows),
        "median_minutes": round(st.median(r["seconds"] for r in rows) / 60, 2),
        "median_turns_to_success": (
            st.median(r["turns_used"] for r in solved) if solved else None
        ),
    }
