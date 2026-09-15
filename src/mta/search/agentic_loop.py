"""Search loops for agentic (tool-misuse) scenarios.

The verifiable judge is free (pure Python), so -- unlike the content track --
there is no expensive judge to gate: every candidate is judged. Cost is only the
target calls (the agent loop) plus the attacker calls.

`run_agentic_single` is the single-turn baseline (the ASR@1 analog): the attacker
proposes N one-shot attacks from the strategy taxonomy, each is run against the
tool-calling target, and the verifiable judge says which broke the scenario. It
is the natural thing to compare against a human writeup: does the auto-attacker
rediscover the manual breaks, and with which strategies?
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

from mta.attacker.propose import LLMProposer
from mta.config import Config
from mta.scenarios.base import Scenario, ScenarioVerdict
from mta.search.budget import Budget
from mta.search.state import Conversation
from mta.targets.agentic import AgenticTarget


@dataclass
class AgenticAttempt:
    strategy: str
    move: str
    verdict: ScenarioVerdict
    tool_sequence: list[str] = field(default_factory=list)


@dataclass
class AgenticRunResult:
    scenario: str
    attempts: list[AgenticAttempt]
    budget: dict

    @property
    def solved(self) -> bool:
        return any(a.verdict.solved for a in self.attempts)

    @property
    def n_solved(self) -> int:
        return sum(1 for a in self.attempts if a.verdict.solved)

    def summary(self) -> str:
        winning = sorted({a.strategy for a in self.attempts if a.verdict.solved})
        # attacks that achieved the misuse but broke the constraint (don't count)
        cheated = sorted(
            {a.strategy for a in self.attempts
             if a.verdict.success and not a.verdict.constraint_ok}
        )
        lines = [
            f"scenario: {self.scenario}",
            f"solved: {'YES' if self.solved else 'no'}  "
            f"({self.n_solved}/{len(self.attempts)} attempts broke it)",
            f"winning strategies: {winning or '-'}",
        ]
        if cheated:
            lines.append(f"reached misuse but violated the constraint (invalid): {cheated}")
        lines.append(f"budget: {self.budget}")
        return "\n".join(lines)


async def run_agentic_single(
    cfg: Config, scenario: Scenario, n_attempts: int
) -> AgenticRunResult:
    budget = Budget(max_target_calls=n_attempts)
    # Single-turn baseline uses only the scenario's single-shot strategies
    # (multi-turn ones need the beam). Fall back to the generic taxonomy.
    scenario_strats = [s for s in (scenario.strategies() or []) if not s.multi_turn]
    proposer = LLMProposer(
        cfg,
        seed=cfg.seed,
        strategies=scenario_strats or None,
        guidance=scenario.attacker_guidance() or "",
    )
    target = AgenticTarget(cfg.target, scenario)

    # One-shot opening attacks conditioned on the strategy taxonomy.
    conv = Conversation(objective=scenario.attacker_objective())
    proposals = await proposer(conv, n_attempts)
    budget.record_attacker_call()

    async def one(move: str, strategy: str) -> AgenticAttempt:
        if not budget.take():
            return None
        result = await target([{"role": "user", "content": move}])
        transcript = [
            {"role": "user", "content": move},
            {"role": "assistant", "content": result.text},
        ]
        verdict = scenario.judge(transcript, result.tool_calls)
        return AgenticAttempt(
            strategy=strategy,
            move=move,
            verdict=verdict,
            tool_sequence=[c.name for c in result.tool_calls],
        )

    attempts = [a for a in await asyncio.gather(*(one(m, s) for m, s in proposals)) if a]
    return AgenticRunResult(scenario=scenario.name, attempts=attempts, budget=budget.summary())


@dataclass
class _Branch:
    attacker_turns: list[str]        # the actual attacker moves (constraint + judge)
    assistant_texts: list[str]       # target's final text per turn (attacker-visible)
    target_history: list[dict]       # full running convo the target sees (no system)
    tool_trace: list                 # accumulated ToolCalls across turns
    strategy_trace: list[str]
    verdict: ScenarioVerdict | None = None


@dataclass
class AgenticBeamResult:
    scenario: str
    solved: bool
    turns: int | None
    best_score: float
    strategy_trace: list[str]
    tool_sequence: list[str]
    reason: str
    budget: dict

    def summary(self) -> str:
        return "\n".join([
            f"scenario: {self.scenario}  (multi-turn beam)",
            f"solved: {'YES' if self.solved else 'no'}"
            + (f" in {self.turns} turn(s)" if self.solved else ""),
            f"best score: {self.best_score:.2f}",
            f"winning strategy trace: {self.strategy_trace}",
            f"tool sequence: {self.tool_sequence}",
            f"reason: {self.reason}",
            f"budget: {self.budget}",
        ])


def _attacker_conv(scenario: Scenario, b: _Branch) -> Conversation:
    """The attacker-visible conversation: its own turns + the target's final text
    replies (so it knows e.g. that turn 1's booking succeeded)."""
    msgs: list[dict] = []
    for u, a in zip(b.attacker_turns, b.assistant_texts):
        msgs.append({"role": "user", "content": u})
        if a:
            msgs.append({"role": "assistant", "content": a})
    return Conversation(objective=scenario.attacker_objective(), messages=tuple(msgs))


async def run_agentic_beam(
    cfg: Config,
    scenario: Scenario,
    beam_width: int = 3,
    depth: int = 2,
    n_proposals: int = 2,
    on_candidate=None,
) -> AgenticBeamResult:
    budget = Budget(max_target_calls=beam_width * n_proposals * depth)
    proposer = LLMProposer(
        cfg, seed=cfg.seed,
        strategies=(scenario.strategies() or None),
        guidance=(scenario.attacker_guidance() or ""),
    )
    target = AgenticTarget(cfg.target, scenario)

    branches = [_Branch([], [], [], [], [])]
    best_score = 0.0
    best_reason = "no misuse"

    for turn in range(depth):
        proposal_lists = await asyncio.gather(
            *(proposer(_attacker_conv(scenario, b), n_proposals) for b in branches)
        )
        for _ in branches:
            budget.record_attacker_call()

        pending: list[tuple[_Branch, str, str]] = []
        for b, props in zip(branches, proposal_lists):
            for move, strat in props:
                if not budget.take():
                    break
                pending.append((b, move, strat))
        if not pending:
            break

        results = await asyncio.gather(
            *(target(b.target_history + [{"role": "user", "content": move}])
              for (b, move, _) in pending)
        )

        scored: list[tuple[float, _Branch]] = []
        for (b, move, strat), result in zip(pending, results):
            attacker_turns = b.attacker_turns + [move]
            tool_trace = b.tool_trace + list(result.tool_calls)
            transcript = [{"role": "user", "content": t} for t in attacker_turns]
            verdict = scenario.judge(transcript, tool_trace)
            nb = _Branch(
                attacker_turns=attacker_turns,
                assistant_texts=b.assistant_texts + [result.text],
                target_history=b.target_history + [{"role": "user", "content": move}] + list(result.messages),
                tool_trace=tool_trace,
                strategy_trace=b.strategy_trace + [strat],
                verdict=verdict,
            )
            scored.append((verdict.score, nb))
            best_score = max(best_score, verdict.score)
            if verdict.score >= best_score:
                best_reason = verdict.reason
            if on_candidate is not None:
                on_candidate({
                    "turn": turn, "strategy": strat, "score": verdict.score,
                    "solved": verdict.solved, "reason": verdict.reason,
                    "tool_sequence": [c.name for c in tool_trace],
                    "move": move,
                })

        scored.sort(key=lambda x: x[0], reverse=True)
        for score, nb in scored:
            if nb.verdict.solved:
                return AgenticBeamResult(
                    scenario=scenario.name, solved=True, turns=turn + 1,
                    best_score=score, strategy_trace=nb.strategy_trace,
                    tool_sequence=[c.name for c in nb.tool_trace],
                    reason=nb.verdict.reason, budget=budget.summary(),
                )
        branches = [nb for _, nb in scored[:beam_width]]

    top = max(branches, key=lambda b: (b.verdict.score if b.verdict else 0.0), default=None)
    return AgenticBeamResult(
        scenario=scenario.name, solved=False, turns=None, best_score=best_score,
        strategy_trace=top.strategy_trace if top else [],
        tool_sequence=[c.name for c in top.tool_trace] if top else [],
        reason=best_reason, budget=budget.summary(),
    )


def write_attempts(result: AgenticRunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for a in result.attempts:
            fh.write(json.dumps({
                "strategy": a.strategy,
                "move": a.move,
                "solved": a.verdict.solved,
                "success": a.verdict.success,
                "constraint_ok": a.verdict.constraint_ok,
                "score": a.verdict.score,
                "reason": a.verdict.reason,
                "tool_sequence": a.tool_sequence,
            }) + "\n")
