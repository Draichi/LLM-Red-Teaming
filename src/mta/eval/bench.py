"""Headline deliverable: single-turn vs multi-turn, across target models.

Runs the single-turn baseline and the multi-turn beam against a scenario for each
target model and produces the one comparison table the project exists to show --
the automated analog of a manual kill log. Because the agentic/injection judges
are verifiable, these ASR numbers carry ~0 false-positive noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mta.config import Config
from mta.scenarios.base import Scenario
from mta.search.agentic_loop import run_agentic_beam, run_agentic_single
from mta.stats import fmt_reliability

# Featherless-only harness: every `org/model` is a Featherless model, including
# `openai/<x>` (the Featherless model whose HF org is "openai", e.g.
# openai/gpt-oss-20b -- NOT the OpenAI API, which is never used here). Only these
# normalize_model lives in mta.providers (leaf module, no import cycles); it is
# re-exported here for the existing callers.
from mta.providers import normalize_model  # noqa: F401


@dataclass
class BenchRow:
    model: str
    single_solved: bool
    single_n_solved: int
    single_attempts: int
    multi_solved: bool
    multi_turns: int | None
    winning_strategies: list[str] = field(default_factory=list)


@dataclass
class BenchResult:
    scenario: str
    rows: list[BenchRow]

    def markdown(self) -> str:
        n = len(self.rows)
        single = sum(1 for r in self.rows if r.single_solved)
        multi = sum(1 for r in self.rows if r.multi_solved)
        lines = [
            f"# Headline: single-turn vs multi-turn ({self.scenario})",
            "",
            f"Verifiable judge (~0 FPR). Targets: {n}.",
            "",
            "| Model | Single-turn (ASR@N) | Multi-turn (beam) | Winning strategy |",
            "|---|---|---|---|",
        ]
        for r in self.rows:
            st = fmt_reliability(r.single_n_solved, r.single_attempts) + (" ✅" if r.single_solved else "")
            mt = ("SOLVED" + (f" ({r.multi_turns}t)" if r.multi_turns else "")) if r.multi_solved else "—"
            strat = "→".join(r.winning_strategies) if r.multi_solved and r.winning_strategies else "—"
            lines.append(f"| `{r.model}` | {st} | {mt} | {strat} |")
        lines += [
            "",
            f"**Single-turn broke {single}/{n} models. Multi-turn broke {multi}/{n}.**",
            "",
            "The gap is the whole thesis: if multi-turn did not clearly beat "
            "single-turn, the premise would be wrong.",
        ]
        return "\n".join(lines)


async def run_bench(
    cfg: Config,
    scenario: Scenario,
    models: list[str],
    attempts: int = 7,
    depth: int = 2,
    beam: int = 3,
    proposals: int = 2,
) -> BenchResult:
    rows: list[BenchRow] = []
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model

        single = await run_agentic_single(mcfg, scenario, attempts)
        multi = await run_agentic_beam(mcfg, scenario, beam_width=beam, depth=depth, n_proposals=proposals)
        rows.append(BenchRow(
            model=model,
            single_solved=single.solved,
            single_n_solved=single.n_solved,
            single_attempts=len(single.attempts),
            multi_solved=multi.solved,
            multi_turns=multi.turns,
            winning_strategies=multi.strategy_trace if multi.solved else [],
        ))
    return BenchResult(scenario=scenario.name, rows=rows)


def write_report(result: BenchResult, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"bench_{result.scenario}.md"
    out.write_text(result.markdown())
    return out
