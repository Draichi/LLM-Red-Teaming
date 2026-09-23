"""Arena-truth store: real Mr. Swan evals as structured calibration data.

The loop the operator asked for: every arena round gets recorded here
(`mta record-eval`); the local judges few-shot against the accumulated truth
(calibration_block, injected into the DecompJudge prompt); each new mining
round grades closer to the arena; each new arena round adds truth. The file
is gitignored work product (real evals, same policy as vectors).

Entries: {scenario, vector, model, axes: {name: score/100}, comment,
response_file?, ts, source}. Score scale: the arena's 0-100.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ARENA_TRUTH_PATH = Path("data/arena_truth.jsonl")


def record_eval(*, scenario: str, vector: str, model: str,
                axes: dict[str, float], comment: str = "",
                response_file: str = "", source: str = "operator-paste",
                path: Path = ARENA_TRUTH_PATH) -> Path:
    rec = {
        "scenario": scenario,
        "vector": vector,
        "model": model,
        "axes": {k: float(v) for k, v in axes.items()},
        "comment": comment[:600],
        "response_file": response_file,
        "source": source,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return Path(path)


def load_truth(scenario: str | None = None,
               path: Path = ARENA_TRUTH_PATH) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return [r for r in rows if scenario is None or r["scenario"] == scenario]


def calibration_block(scenario: str, limit: int = 4,
                      path: Path = ARENA_TRUTH_PATH) -> str:
    """Real arena judge dispositions for the DESIGN-JUDGE to grade
    consistently with. Response texts are included when the recording stored
    them (full few-shot grading); otherwise axes + comment are rubric
    anchors."""
    rows = load_truth(scenario, path)[-limit:]
    if not rows:
        return ""
    lines = ["Arena judge calibration (real Mr. Swan evals on THIS scenario - "
             "grade consistently with these dispositions):"]
    for r in rows:
        axes = ", ".join(f"{k}={v:.0f}" for k, v in r["axes"].items())
        lines.append(f"- [{r['vector']} on {r['model']}] axes: {axes}"
                     + (f" | judge: {r['comment'][:220]}" if r["comment"] else ""))
    return "\n".join(lines)
