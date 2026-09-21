"""Scenario plugins: one per Gray Swan objective *type*.

The MTA core (beam search, attacker, gate, budget) is scenario-agnostic. What
changes per scenario type is two pluggable pieces:

  * the TARGET setup (chat / tool-calling agent / injection app / multimodal), and
  * the JUDGE (fuzzy content rubric, or -- for agentic / injection scenarios -- a
    VERIFIABLE predicate on what the target actually did, which has ~0 FPR and
    sidesteps the LLM-judge calibration ceiling entirely).

A `Scenario` bundles the environment (system prompt + tools), what the attacker
is told to achieve, and the verifiable judge (success predicate + the scenario's
constraints, e.g. "no impersonation").
"""

from mta.scenarios.americium_extraction import AmericiumExtractionScenario
from mta.scenarios.base import (
    Scenario,
    ScenarioVerdict,
    ToolCall,
    TurnResult,
)
from mta.scenarios.dll_injection import DllInjectionScenario
from mta.scenarios.email_ignore import EmailIgnoreScenario
from mta.scenarios.hotel_booking import HotelBookingScenario
from mta.scenarios.malware_game import MalwareGameScenario
from mta.scenarios.radical_propaganda import RadicalPropagandaScenario
from mta.scenarios.ransomware_injection import RansomwareInjectionScenario
from mta.scenarios.secret_extraction import SecretExtractionScenario
from mta.scenarios.teacher_msg import TeacherMsgScenario

# Registry: scenario name -> constructor. Add a new Gray Swan scenario type here.
SCENARIOS = {
    "hotel_booking": HotelBookingScenario,            # agentic tool-misuse
    "secret_extraction": SecretExtractionScenario,    # direct prompt injection (chat)
    "ransomware_injection": RansomwareInjectionScenario,  # indirect prompt injection
    "malware_game": MalwareGameScenario,              # indirect prompt injection (malware rec)
    "email_ignore": EmailIgnoreScenario,              # indirect (poisoned inbox -> deny emails)
    "radical_propaganda": RadicalPropagandaScenario,  # chat content-gen (rubric + constraints)
    "dll_injection": DllInjectionScenario,            # chat content-gen (per-axis arena judge)
    "americium_extraction": AmericiumExtractionScenario,  # chat content-gen (fuzzy, 3 axes)
    "teacher_msg": TeacherMsgScenario,                  # agentic tool-misuse (verifiable)
}


def get_scenario(name: str) -> Scenario:
    try:
        return SCENARIOS[name]()
    except KeyError:
        raise ValueError(
            f"unknown scenario {name!r}; known: {list(SCENARIOS)}"
        ) from None


__all__ = [
    "Scenario", "ScenarioVerdict", "ToolCall", "TurnResult",
    "SCENARIOS", "get_scenario",
]
