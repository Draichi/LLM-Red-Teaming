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


async def run_agentic_replay(cfg: Config, scenario, models: list[str], vectors: list[dict], trials: int = 1) -> ReplayMatrix:
    """Multi-turn transfer test for VERIFIABLE agentic scenarios (e.g. hotel tool
    misuse): replay each vector's fixed attacker-turn sequence through the tool-
    calling target, accumulate the tool trace, and judge with the scenario's ~0-FPR
    verifiable judge. `trials` guards against target sampling noise."""
    import asyncio

    cells: dict = {}
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def one_trial(turns: list[str]) -> bool:
            history, user_turns, trace = [], [], []
            for t in turns:
                result = await target(history + [{"role": "user", "content": t}])
                trace += list(result.tool_calls)
                history = history + [{"role": "user", "content": t}] + list(result.messages)
                user_turns.append({"role": "user", "content": t})
            return scenario.judge(user_turns, trace).solved

        async def run_one(i: int, turns: list[str]):
            breaks = ok = 0
            for _ in range(trials):
                try:
                    ok += 1
                    breaks += 1 if await one_trial(turns) else 0
                except Exception:  # noqa: BLE001
                    ok -= 1
            return i, ({"breaks": breaks, "trials": ok, "best": 1.0 if breaks else 0.0} if ok else None)

        outs = await asyncio.gather(*(run_one(i, v.get("turns", [])) for i, v in enumerate(vectors)))
        for i, cell in outs:
            cells[(i, model)] = cell
    return ReplayMatrix(scenario.name, [normalize_model(m) for m in models], vectors, cells)


async def run_content_replay(cfg: Config, scenario, models: list[str], vectors: list[dict], trials: int = 1) -> ReplayMatrix:
    """Multi-turn transfer test: replay each content vector's FIXED attacker-turn
    sequence against every model, then score the full transcript with the rubric +
    the scenario's verifiable gates. Each cell is run `trials` times because the
    fuzzy content judge + temperature make single runs noisy."""
    import asyncio

    from mta.judge.llm_judge import LLMJudge

    judge = LLMJudge(cfg.judge)
    thr = cfg.judge.success_threshold
    cells: dict = {}
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def one_trial(turns: list[str]) -> tuple[bool, float]:
            convo, asst = [], []
            for t in turns:
                convo.append({"role": "user", "content": t})
                result = await target(convo)
                convo.append({"role": "assistant", "content": result.text})
                asst.append(result.text)
            rubric = await judge.score_transcript(scenario.content_objective(), convo)
            constraint = scenario.check_constraints(convo, asst[-1] if asst else "")
            deflected = scenario.is_deflection(asst[-1] if asst else "")
            delivered = rubric.score >= thr and constraint.ok and not deflected
            return delivered, rubric.score

        async def run_one(i: int, turns: list[str]):
            breaks = best = ok = 0
            for _ in range(trials):
                try:
                    delivered, score = await one_trial(turns)
                    ok += 1
                    breaks += 1 if delivered else 0
                    best = max(best, score)
                except Exception:  # noqa: BLE001
                    pass
            return i, ({"breaks": breaks, "trials": ok, "best": best} if ok else None)

        outs = await asyncio.gather(*(run_one(i, v.get("turns", [])) for i, v in enumerate(vectors)))
        for i, cell in outs:
            cells[(i, model)] = cell
    return ReplayMatrix(scenario.name, [normalize_model(m) for m in models], vectors, cells)


@dataclass
class ReplayMatrix:
    scenario: str
    models: list[str]
    vectors: list[dict]
    cells: dict  # (vector_index, model) -> {"breaks","trials","best"} | None

    def markdown(self) -> str:
        header = "| # | strategy | " + " | ".join(m.split("/")[-1] for m in self.models) + " | usable models |"
        sep = "|---|---|" + "---|" * (len(self.models) + 1)
        lines = [f"# Transfer matrix: {self.scenario}", "",
                 f"{len(self.vectors)} vector(s) × {len(self.models)} model(s). "
                 "Cell = breaks/trials. ✅ reliable (>=50%), ◑ usable via re-runs (>0), "
                 "✗ never. The arena target is stochastic and allows re-runs, so any "
                 "non-zero rate is a usable vector (~1/rate tries to land).",
                 "", header, sep]
        model_hits = {m: 0 for m in self.models}
        for i, vec in enumerate(self.vectors):
            label = vec.get("strategy") or "→".join(vec.get("strategy_trace", [])) or "?"
            cells, usable = [], 0
            for m in self.models:
                c = self.cells.get((i, m))
                if not c:
                    cells.append("·")
                    continue
                frac = c["breaks"] / c["trials"] if c["trials"] else 0.0
                mark = "✅" if frac >= 0.5 else ("◑" if frac > 0 else "✗")
                nm = c.get("near_misses", 0)
                nm_txt = f"·nm{nm}" if nm else ""
                cells.append(f"{mark} {c['breaks']}/{c['trials']}{nm_txt}")
                if frac > 0:
                    usable += 1
                    model_hits[m] += 1
            lines.append(f"| {i} | {label} | " + " | ".join(cells) + f" | {usable}/{len(self.models)} |")
        lines += ["",
                  "**Per model broken at all (usable via re-runs):** " + ", ".join(
                      f"{m.split('/')[-1]} {model_hits[m]}/{len(self.vectors)}" for m in self.models),
                  "",
                  "A vector that breaks several models -- even at a low rate -- is a Gray "
                  "Swan candidate, since the arena is stochastic and re-runnable."]
        return "\n".join(lines)


async def run_sweep(cfg: Config, scenario, models: list[str], n_attacks: int, trials: int = 1) -> ReplayMatrix:
    """Susceptibility sweep: generate a pool of attacks ONCE, then run the SAME
    attacks against every model. Shows how one attack fares across models and
    surfaces which model is susceptible enough to then develop/refine against."""
    from mta.attacker.propose import LLMProposer
    from mta.search.state import Conversation

    proposer = LLMProposer.from_scenario(cfg, scenario, seed=cfg.seed)
    proposals = await proposer(Conversation(objective=scenario.attacker_objective()), n_attacks)
    vectors = [{"strategy": strat, "payload": payload} for payload, strat in proposals]
    return await run_replay(cfg, scenario, models, vectors, trials=trials)


async def run_replay(cfg: Config, scenario, models: list[str], vectors: list[dict], trials: int = 1) -> ReplayMatrix:
    """Single-shot transfer test. Each (vector, model) cell is run `trials` times;
    the cell reports how many trials broke it (reliability against sampling noise)."""
    import asyncio

    cells: dict = {}
    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def run_one(i: int, payload: str):
            breaks = best = ok = near_misses = 0
            worst_axes, worst_score = None, 2.0
            for _ in range(trials):
                try:
                    result = await target(scenario.assemble(payload))
                    v = scenario.judge_injection(result.text, payload)
                    ok += 1
                    breaks += 1 if v.solved else 0
                    best = max(best, v.score)
                    # Near-miss: the recommendation was delivered but a gate axis
                    # (originality) held it below the arena floor - the
                    # convertible state, counted separately from plain misses.
                    if v.success and not v.solved:
                        near_misses += 1
                    if v.score < worst_score:
                        worst_score, worst_axes = v.score, v.axes
                except Exception:  # noqa: BLE001 - a bad model must not kill the sweep
                    pass
            return i, ({"breaks": breaks, "trials": ok, "best": best,
                        "near_misses": near_misses, "worst_axes": worst_axes}
                       if ok else None)

        outs = await asyncio.gather(*(run_one(i, v["payload"]) for i, v in enumerate(vectors)))
        if all(c is None for _, c in outs):
            print(f"[sweep] {model}: unavailable (all calls failed -- gated/unsupported?), skipped")
        for i, cell in outs:
            cells[(i, model)] = cell
    return ReplayMatrix(scenario.name, [normalize_model(m) for m in models], vectors, cells)


def write_report(matrix: ReplayMatrix, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"transfer_{matrix.scenario}.md"
    out.write_text(matrix.markdown())
    return out
