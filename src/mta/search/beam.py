"""Beam search: the loop the judge is a value function for.

At each depth, expand every live beam into `n_proposals` candidate next turns
(strategy-conditioned attacker moves), query the target, drop obvious refusals
with the cheap gate, score survivors with the LLM judge, and keep the top
`beam_width`. Stop early on a success, or when the target-call budget runs out.

The attacker `propose` and the target `__call__` are injected, so the same loop
runs against a local model or an API model, with any attacker policy.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from mta.config import SearchConfig
from mta.judge.cheap_filter import is_obvious_refusal
from mta.judge.llm_judge import LLMJudge
from mta.search.budget import Budget
from mta.search.state import Conversation, RunResult

# An attacker proposal: the next user turn plus the strategy label that produced
# it. `propose(conversation, n) -> [(user_message, strategy_label), ...]`.
Proposal = tuple[str, str]
ProposeFn = Callable[[Conversation, int], Awaitable[list[Proposal]]]
# A target: `target(messages) -> assistant_reply`.
TargetFn = Callable[[list[dict]], Awaitable[str]]


async def beam_search(
    objective: str,
    target: TargetFn,
    propose: ProposeFn,
    judge: LLMJudge,
    cfg: SearchConfig,
    on_candidate: Callable[[dict], None] | None = None,
) -> RunResult:
    budget = Budget(max_target_calls=cfg.max_target_calls)
    judge.budget = budget
    beams: list[Conversation] = [Conversation(objective=objective)]
    best_score = 0.0

    for turn in range(cfg.depth):
        # 1. Propose next moves for every live beam.
        proposal_lists = await asyncio.gather(
            *(propose(conv, cfg.n_proposals) for conv in beams)
        )
        for _ in beams:
            budget.record_attacker_call()

        pending: list[tuple[Conversation, str, str]] = []  # (conv, move, strategy)
        for conv, proposals in zip(beams, proposal_lists):
            for move, strategy in proposals:
                if not budget.take():
                    break
                pending.append((conv, move, strategy))

        if not pending:
            return _result(objective, False, "budget_exhausted", best_score, budget)

        # 2. Query the target for each pending move.
        async def _ask(conv: Conversation, move: str) -> str:
            msgs = conv.as_list() + [{"role": "user", "content": move}]
            return await target(msgs)

        replies = await asyncio.gather(*(_ask(c, m) for c, m, _ in pending))

        # 3. Cheap gate, then build candidate conversations.
        candidates: list[Conversation] = []
        for (conv, move, strategy), reply in zip(pending, replies):
            if is_obvious_refusal(reply):
                continue
            candidates.append(
                conv.extend(
                    {"role": "user", "content": move},
                    {"role": "assistant", "content": reply},
                    strategy=strategy,
                )
            )

        if not candidates:
            if budget.exhausted:
                return _result(objective, False, "budget_exhausted", best_score, budget)
            # everything refused this depth; nothing to expand
            return _result(objective, False, "all_branches_refused", best_score, budget)

        # 4. Judge survivors.
        verdicts = await asyncio.gather(
            *(judge.score_transcript(objective, c.as_list()) for c in candidates)
        )
        ranked = sorted(
            zip(verdicts, candidates), key=lambda x: x[0].score, reverse=True
        )

        for verdict, conv in ranked:
            best_score = max(best_score, verdict.score)
            if on_candidate is not None:
                on_candidate(
                    {
                        "objective": objective,
                        "depth": turn,
                        "score": verdict.score,
                        "verdict": verdict.model_dump(),
                        "transcript": conv.as_list(),
                        "strategy_trace": list(conv.strategy_trace),
                    }
                )

        top_verdict, top_conv = ranked[0]
        if top_verdict.score >= judge.cfg.success_threshold:
            return RunResult(
                objective=objective,
                solved=True,
                turns=turn + 1,
                reason="success",
                best_score=top_verdict.score,
                transcript=top_conv.as_list(),
                strategy_trace=list(top_conv.strategy_trace),
                budget=budget.summary(),
            )

        beams = [c for _, c in ranked[: cfg.beam_width]]

    return _result(objective, False, "budget_exhausted", best_score, budget)


def _result(objective, solved, reason, best_score, budget) -> RunResult:
    return RunResult(
        objective=objective,
        solved=solved,
        reason=reason,
        best_score=best_score,
        budget=budget.summary(),
    )
