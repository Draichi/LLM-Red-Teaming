"""Replay validated vectors across models -- the transfer matrix.

Takes the payloads in the local vector library (data/vectors/<scenario>.jsonl) and
runs each one against several target models, so the same attack's behavior across
models is visible at a glance. This is how a vector earns its place in the Gray
Swan kit: one that breaks several independent models is a strong bet against the
arena's unknown target.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mta.config import Config
from mta.eval.bench import normalize_model
from mta.targets.agentic import AgenticTarget

VECTORS_DIR = Path("data/vectors")


def load_vectors(scenario_name: str, limit: int | None = None) -> list[dict]:
    """Load unique vectors from the local library (most recent first). A vector is
    keyed by its single-shot `payload` or, for multi-turn content vectors, the
    tuple of `turns`."""
    path = VECTORS_DIR / f"{scenario_name}.jsonl"
    if not path.exists():
        return []
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    seen, out = set(), []
    for r in reversed(rows):  # newest first
        key = r.get("payload") or tuple(r.get("turns", []))
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out[:limit] if limit else out


async def run_content_replay(cfg: Config, scenario, models: list[str], vectors: list[dict]) -> ReplayMatrix:
    """Multi-turn transfer test: replay each content vector's FIXED attacker-turn
    sequence against every model, then score the full transcript with the rubric +
    the scenario's verifiable gates. Shows how a conversational attack transfers."""
    import asyncio

    from mta.judge.llm_judge import LLMJudge
    from mta.scenarios.base import ScenarioVerdict

    judge = LLMJudge(cfg.judge)
    thr = cfg.judge.success_threshold
    cells: dict = {}
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def run_one(i: int, turns: list[str]):
            try:
                convo, atk, asst = [], [], []
                for t in turns:
                    convo.append({"role": "user", "content": t})
                    result = await target(convo)
                    convo.append({"role": "assistant", "content": result.text})
                    atk.append(t)
                    asst.append(result.text)
                transcript = convo
                rubric = await judge.score_transcript(scenario.content_objective(), transcript)
                constraint = scenario.check_constraints(transcript, asst[-1] if asst else "")
                deflected = scenario.is_deflection(asst[-1] if asst else "")
                delivered = rubric.score >= thr and not deflected
                score = rubric.score if (constraint.ok and not deflected) else min(rubric.score, 0.4)
                return i, ScenarioVerdict(success=delivered, constraint_ok=constraint.ok,
                                          score=round(score, 3), reason="", detail={})
            except Exception:  # noqa: BLE001 - a bad model must not kill the sweep
                return i, None

        outs = await asyncio.gather(*(run_one(i, v.get("turns", [])) for i, v in enumerate(vectors)))
        for i, verdict in outs:
            cells[(i, model)] = verdict
    return ReplayMatrix(scenario.name, [normalize_model(m) for m in models], vectors, cells)


@dataclass
class ReplayMatrix:
    scenario: str
    models: list[str]
    vectors: list[dict]
    cells: dict  # (vector_index, model) -> verdict

    def markdown(self) -> str:
        header = "| # | strategy | " + " | ".join(m.split("/")[-1] for m in self.models) + " | transfers |"
        sep = "|---|---|" + "---|" * (len(self.models) + 1)
        lines = [f"# Transfer matrix: {self.scenario}", "",
                 f"{len(self.vectors)} vector(s) × {len(self.models)} model(s). "
                 f"Cell = ✅ solved / score.", "", header, sep]
        model_hits = {m: 0 for m in self.models}
        for i, vec in enumerate(self.vectors):
            label = vec.get("strategy") or "→".join(vec.get("strategy_trace", [])) or "?"
            cells = []
            transfers = 0
            for m in self.models:
                v = self.cells.get((i, m))
                if v is None:
                    cells.append("·")
                elif v.solved:
                    cells.append("✅")
                    transfers += 1
                    model_hits[m] += 1
                else:
                    cells.append(f"{v.score:.1f}")
            lines.append(f"| {i} | {label} | " + " | ".join(cells) + f" | {transfers}/{len(self.models)} |")
        lines += ["",
                  "**Per model broken by:** " + ", ".join(
                      f"{m.split('/')[-1]} {model_hits[m]}/{len(self.vectors)}" for m in self.models),
                  "",
                  "A vector that transfers across several models is a strong Gray Swan candidate."]
        return "\n".join(lines)


async def run_sweep(cfg: Config, scenario, models: list[str], n_attacks: int) -> ReplayMatrix:
    """Susceptibility sweep: generate a pool of attacks ONCE, then run the SAME
    attacks against every model. Shows how one attack fares across models and
    surfaces which model is susceptible enough to then develop/refine against."""
    from mta.attacker.propose import LLMProposer
    from mta.search.state import Conversation

    proposer = LLMProposer(
        cfg, seed=cfg.seed,
        strategies=(scenario.strategies() or None),
        guidance=(scenario.attacker_guidance() or ""),
    )
    proposals = await proposer(Conversation(objective=scenario.attacker_objective()), n_attacks)
    vectors = [{"strategy": strat, "payload": payload} for payload, strat in proposals]
    return await run_replay(cfg, scenario, models, vectors)


async def run_replay(cfg: Config, scenario, models: list[str], vectors: list[dict]) -> ReplayMatrix:
    import asyncio

    cells: dict = {}
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def run_one(i: int, payload: str):
            try:
                result = await target(scenario.assemble(payload))
                return i, scenario.judge_injection(result.text, payload)
            except Exception as e:  # noqa: BLE001 - a bad model must not kill the sweep
                return i, None  # unavailable (gated/error); rendered as "·"

        outs = await asyncio.gather(*(run_one(i, v["payload"]) for i, v in enumerate(vectors)))
        n_ok = sum(1 for _, verdict in outs if verdict is not None)
        if n_ok == 0:
            print(f"[sweep] {model}: unavailable (all calls failed -- gated/unsupported?), skipped")
        for i, verdict in outs:
            cells[(i, model)] = verdict
    return ReplayMatrix(scenario.name, [normalize_model(m) for m in models], vectors, cells)


def write_report(matrix: ReplayMatrix, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"transfer_{matrix.scenario}.md"
    out.write_text(matrix.markdown())
    return out
