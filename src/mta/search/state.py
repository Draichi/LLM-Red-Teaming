"""Search state: conversations, candidates, run results.

Conversations are immutable-ish: extending one returns a new Conversation so the
beam can branch without aliasing. Every candidate the search evaluates is written
to JSONL (see eval.run_loop), so runs are resumable and the full search tree is
available for the writeup.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Conversation:
    """A conversation being grown toward an objective."""

    objective: str
    messages: tuple[dict, ...] = ()
    strategy_trace: tuple[str, ...] = ()  # strategy label used at each attacker turn
    # Judge/verdict context threaded to the attacker (e.g. per-axis scores +
    # binding axis for mechanism repair). Not part of identity/equality.
    meta: dict = field(default_factory=dict, compare=False)

    def extend(self, *new_messages: dict, strategy: str | None = None) -> "Conversation":
        trace = self.strategy_trace + ((strategy,) if strategy else ())
        return Conversation(
            objective=self.objective,
            messages=self.messages + tuple(new_messages),
            strategy_trace=trace,
            meta=dict(self.meta),
        )

    def as_list(self) -> list[dict]:
        return list(self.messages)

    @property
    def n_turns(self) -> int:
        return sum(1 for m in self.messages if m.get("role") == "user")


@dataclass
class Candidate:
    conversation: Conversation
    score: float
    verdict: Optional[dict] = None  # JudgeVerdict.model_dump()
    created_at: float = field(default_factory=time.time)


@dataclass
class RunResult:
    objective: str
    solved: bool
    turns: Optional[int] = None
    reason: str = ""
    best_score: float = 0.0
    transcript: Optional[list[dict]] = None
    strategy_trace: Optional[list[str]] = None
    budget: Optional[dict] = None

    def to_json(self) -> dict:
        return {
            "objective": self.objective,
            "solved": self.solved,
            "turns": self.turns,
            "reason": self.reason,
            "best_score": self.best_score,
            "transcript": self.transcript,
            "strategy_trace": self.strategy_trace,
            "budget": self.budget,
        }
