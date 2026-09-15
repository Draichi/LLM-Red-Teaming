"""Call accounting and hard caps.

Every target/attacker/judge call goes through here so a run's cost is a fact,
not a guess, and so ASR is always reported at a fixed, enforced budget. `take()`
is the gate the beam checks before spending a target call.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Budget:
    max_target_calls: int
    target_calls: int = 0
    attacker_calls: int = 0
    judge_calls: int = 0
    gate_calls: int = 0       # second-tier classifier gate invocations
    gate_filtered: int = 0    # of those, how many were screened out
    # optional per-component wall-clock, filled by callers if they time calls
    seconds: dict[str, float] = field(default_factory=dict)

    def take(self) -> bool:
        """Reserve one target call. Returns False if the cap is reached."""
        if self.target_calls >= self.max_target_calls:
            return False
        self.target_calls += 1
        return True

    def record_attacker_call(self) -> None:
        self.attacker_calls += 1

    def record_judge_call(self) -> None:
        self.judge_calls += 1

    def record_gate_call(self) -> None:
        self.gate_calls += 1

    def record_gate_filtered(self) -> None:
        self.gate_filtered += 1

    def add_seconds(self, component: str, secs: float) -> None:
        self.seconds[component] = self.seconds.get(component, 0.0) + secs

    @property
    def exhausted(self) -> bool:
        return self.target_calls >= self.max_target_calls

    def summary(self) -> dict:
        return {
            "target_calls": self.target_calls,
            "attacker_calls": self.attacker_calls,
            "judge_calls": self.judge_calls,
            "gate_calls": self.gate_calls,
            "gate_filtered": self.gate_filtered,
            "seconds": dict(self.seconds),
        }
