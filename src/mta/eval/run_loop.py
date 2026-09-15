"""Run the beam-search loop (and the single-turn baseline) over the objective set.

Every candidate the search evaluates is streamed to JSONL as it happens, so runs
are resumable and the full search tree survives for the writeup. Objectives are
one JSON object per line in `data/behaviors/objectives.jsonl` with at least an
`objective` field.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mta.attacker.propose import LLMProposer
from mta.config import Config
from mta.judge.cheap_filter import is_obvious_refusal
from mta.judge.llm_judge import LLMJudge
from mta.search.beam import beam_search
from mta.search.state import RunResult
from mta.targets.base import build_target


def load_objectives(path: str | Path) -> list[str]:
    objs = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        objs.append(json.loads(line)["objective"])
    return objs


def _jsonl_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a")

    def write(record: dict) -> None:
        fh.write(json.dumps(record) + "\n")
        fh.flush()

    return write, fh


def _build_gate(cfg: Config):
    if not cfg.gate.enabled:
        return None
    from mta.judge.classifier_gate import LLMClassifierGate

    return LLMClassifierGate(cfg.gate)


async def run_beam(cfg: Config, objectives: list[str]) -> list[RunResult]:
    target = build_target(cfg.target)
    judge = LLMJudge(cfg.judge)
    proposer = LLMProposer(cfg, seed=cfg.seed)
    gate = _build_gate(cfg)
    write, fh = _jsonl_writer(cfg.runs_dir / "beam_candidates.jsonl")
    try:
        results = []
        for obj in objectives:
            res = await beam_search(
                obj, target, proposer, judge, cfg.search, on_candidate=write, gate=gate
            )
            results.append(res)
            write({"kind": "result", **res.to_json()})
        return results
    finally:
        fh.close()


async def run_single_turn(cfg: Config, objectives: list[str]) -> list[RunResult]:
    """Phase 3 floor: one plain single-turn attempt per objective. If beam search
    does not clearly beat this, the multi-turn premise is wrong."""
    target = build_target(cfg.target)
    judge = LLMJudge(cfg.judge)
    gate = _build_gate(cfg)
    thr = cfg.judge.success_threshold

    async def one(obj: str) -> RunResult:
        messages = [{"role": "user", "content": obj}]
        reply = await target(messages)
        if is_obvious_refusal(reply):
            return RunResult(obj, solved=False, turns=1, reason="refused", best_score=0.0)
        if gate is not None and await gate.is_refusal(obj, reply):
            return RunResult(obj, solved=False, turns=1, reason="gate_refused", best_score=0.0)
        messages.append({"role": "assistant", "content": reply})
        v = await judge.score_transcript(obj, messages)
        return RunResult(
            obj,
            solved=v.score >= thr,
            turns=1,
            reason="success" if v.score >= thr else "below_threshold",
            best_score=v.score,
            transcript=messages,
        )

    return list(await asyncio.gather(*(one(o) for o in objectives)))


def asr(results: list[RunResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r.solved) / len(results)
