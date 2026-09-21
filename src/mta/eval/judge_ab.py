"""Judge A/B on identical transcripts (item 2 acceptance).

Plays each saved vector's turns against a target ONCE, grades the captured
transcript with BOTH the scenario's current judge (AxisJudge, or whatever
resolve_content_judge picks) and the decompositional judge, and writes the
disagreement table to reports/judge_ab_<scenario>.md. Same transcript for both
judges is the point: any score difference is attributable to the judge, not
the target's sampling noise. Rows where `solved` disagrees are the hand-
inspection queue.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mta.config import Config
from mta.eval.bench import normalize_model
from mta.judge.decompositional import (
    DecompJudge,
    decomposition_for,
    resolve_content_judge,
)
from mta.targets.agentic import AgenticTarget


@dataclass
class ABRow:
    index: int
    strategy: str
    turns: int
    baseline_name: str
    baseline_score: float
    baseline_solved: bool
    baseline_binding: str
    decomp_score: float
    decomp_solved: bool
    decomp_binding: str
    decomp_axes: dict = field(default_factory=dict)

    @property
    def disagree(self) -> bool:
        return self.baseline_solved != self.decomp_solved


@dataclass
class ABResult:
    scenario: str
    model: str
    rows: list[ABRow]

    def markdown(self) -> str:
        n = len(self.rows)
        disagreements = [r for r in self.rows if r.disagree]
        lines = [
            f"# Judge A/B: {self.scenario}",
            "",
            f"Target: `{self.model}` ({n} vector(s), one transcript each, both "
            "judges grading the identical text). Rows where `solved` differs are "
            "the hand-inspection queue -- log the verdict in the scenario writeup.",
            "",
            "| # | strategy | turns | baseline judge | baseline | decomp | decomp axes | disagree |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in self.rows:
            mark = "**YES**" if r.disagree else ""
            lines.append(
                f"| {r.index} | {r.strategy} | {r.turns} | {r.baseline_name} "
                f"| {r.baseline_score:.2f} {'PASS' if r.baseline_solved else 'fail'}"
                f" ({r.baseline_binding or '-'}) "
                f"| {r.decomp_score:.2f} {'PASS' if r.decomp_solved else 'fail'}"
                f" ({r.decomp_binding or '-'}) "
                f"| {r.decomp_axes} | {mark} |")
        lines += ["",
                  f"**{len(disagreements)}/{n} disagree.**"]
        if disagreements:
            decomp_harsher = sum(1 for r in disagreements if r.baseline_solved)
            lines.append(
                f"Baseline says PASS where decomp says fail: {decomp_harsher}; "
                f"the reverse: {len(disagreements) - decomp_harsher}. A decomp-harsher "
                "direction is the expected signature -- holistic judges overestimate.")
        return "\n".join(lines) + "\n"


async def run_judge_ab(cfg: Config, scenario, model: str,
                       vectors: list[dict]) -> ABResult:
    """Play each vector once, grade the transcript with both judges."""
    decomp = decomposition_for(scenario.name)
    if decomp is None:
        raise ValueError(
            f"no configs/decomposition/{scenario.name}.yaml -- judge-ab needs a "
            f"decomposition to compare against")
    mcfg = cfg.model_copy(deep=True)
    mcfg.target.model = normalize_model(model)
    target = AgenticTarget(mcfg.target, scenario)
    baseline = resolve_content_judge(cfg, scenario)
    d_judge = DecompJudge(cfg.judge, decomp)

    async def play(turns: list[str]) -> list[dict]:
        convo: list[dict] = []
        for t in turns:
            convo.append({"role": "user", "content": t})
            result = await target(convo)
            convo.append({"role": "assistant", "content": result.text})
        return convo

    rows: list[ABRow] = []
    for i, vec in enumerate(vectors):
        turns = vec.get("turns") or [vec.get("payload", "")]
        convo = await play([t for t in turns if t])
        objective = (scenario.content_objective() if hasattr(scenario, "content_objective")
                     else scenario.attacker_objective())
        bv = await baseline.score_transcript(objective, convo)
        dv = await d_judge.score_transcript(objective, convo)
        rows.append(ABRow(
            index=i,
            strategy=vec.get("strategy") or "→".join(vec.get("strategy_trace", [])) or "?",
            turns=len(turns),
            baseline_name=type(baseline).__name__,
            baseline_score=round(bv.score, 3),
            baseline_solved=bool(getattr(bv, "solved", bv.score >= cfg.judge.success_threshold)),
            baseline_binding=getattr(bv, "binding_axis", ""),
            decomp_score=round(dv.score, 3),
            decomp_solved=dv.solved,
            decomp_binding=dv.binding_axis,
            decomp_axes={k: v for k, v in dv.axes.items()},
        ))
    return ABResult(scenario=scenario.name, model=mcfg.target.model, rows=rows)


def write_report(result: ABResult, reports_dir: Path) -> Path:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"judge_ab_{result.scenario}.md"
    out.write_text(result.markdown())
    return out
