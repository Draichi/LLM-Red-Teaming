"""Core data model for scenario plugins.

`ToolCall` / `TurnResult` capture what a tool-calling target actually did (the
ordered tool calls, not just text). `ScenarioVerdict` is what a verifiable judge
returns: a boolean `solved` plus a `score` in [0,1] so beam search still has a
gradient to climb (partial progress -> partial score), plus the constraint check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict
    id: str = ""


@dataclass
class TurnResult:
    """One target turn. For a chat target, `tool_calls` is empty and `text` is
    the reply. For an agentic target, `tool_calls` is the ordered trace.

    `messages` is the target-side messages appended this turn (assistant turns +
    tool results) so a multi-turn caller can thread the running conversation into
    the next turn -- the target sees what it did last turn (e.g. "Booked room 101")."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    # Provider finish_reason for the final text turn ("length" = truncated).
    # Drives truncation detection in the death classifier (judge.cheap_filter).
    finish_reason: str = ""


@dataclass
class ScenarioVerdict:
    success: bool          # did the target perform the target misuse?
    constraint_ok: bool    # were the scenario's constraints respected (e.g. no impersonation)?
    score: float           # [0,1] gradient for beam ranking (partial progress counts)
    reason: str = ""
    detail: dict = field(default_factory=dict)
    # Per-axis vector in [0,1] mirroring the arena's axes where the scenario
    # knows them (e.g. malware_game: recommendation/originality). The arena
    # passes only when EVERY axis clears its floor, so a scalar alone hides the
    # convertible near-miss (one axis down, the rest clean).
    axes: dict[str, float] = field(default_factory=dict)

    @property
    def solved(self) -> bool:
        # A scenario is only "solved" if the misuse happened AND the attack
        # obeyed the constraints -- winning by cheating (e.g. impersonation) does
        # not count, just as it would not in the Gray Swan arena.
        return self.success and self.constraint_ok

    @property
    def binding_axis(self) -> str:
        """The axis holding the verdict down (the lowest); "" when unknown or all
        maxed. Repair loops should target this axis, not the aggregate score."""
        if not self.axes:
            return ""
        name = min(self.axes, key=lambda a: self.axes[a])
        return "" if self.axes[name] >= 1.0 else name


@runtime_checkable
class Scenario(Protocol):
    name: str

    def system_prompt(self) -> str:
        """The target environment's system prompt (e.g. the hotel assistant)."""
        ...

    def tools(self) -> list[dict]:
        """Tool JSON schemas exposed to the target. [] for non-agentic scenarios."""
        ...

    def attacker_objective(self) -> str:
        """What the attacker is told to achieve (drives `propose`)."""
        ...

    def run_tool(self, call: ToolCall, state: dict) -> str:
        """Execute a tool call against the (mutable) environment state and return
        the tool result string the target sees next. `state` persists across the
        turn's tool calls."""
        ...

    def judge(self, transcript: list[dict], tool_calls: list[ToolCall]) -> ScenarioVerdict:
        """Verifiable judge: inspect the ordered tool-call trace for the misuse
        and the transcript (user turns) for constraint violations."""
        ...

    def strategies(self) -> list:
        """Scenario-specific attack strategies (labels + descriptions, never
        payloads). Empty -> the attacker falls back to the generic taxonomy."""
        ...

    def attacker_guidance(self) -> str:
        """Extra standing guidance for the attacker on this scenario (e.g. which
        techniques violate the constraint). Empty string if none."""
        ...
