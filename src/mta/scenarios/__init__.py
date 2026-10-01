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
from mta.scenarios.cheat_on_exam import CheatOnExamScenario
from mta.scenarios.cyanide_extraction import CyanideExtractionScenario
from mta.scenarios.discount_code_500 import DiscountCode500Scenario
from mta.scenarios.dll_injection import DllInjectionScenario
from mta.scenarios.drug_dealer_search import DrugDealerSearchScenario
from mta.scenarios.reveal_override_code import RevealOverrideCodeScenario
from mta.scenarios.email_ignore import EmailIgnoreScenario
from mta.scenarios.fraud_disclosure import FraudDisclosureScenario
from mta.scenarios.hotel_booking import HotelBookingScenario
from mta.scenarios.malware_game import MalwareGameScenario
from mta.scenarios.radical_propaganda import RadicalPropagandaScenario
from mta.scenarios.ransomware_injection import RansomwareInjectionScenario
from mta.scenarios.secret_extraction import SecretExtractionScenario
from mta.scenarios.sportscar_offer import SportscarOfferScenario
from mta.scenarios.teacher_msg import TeacherMsgScenario
from mta.scenarios.prescription_exfil import PrescriptionExfilScenario
from mta.scenarios.utility_shutoff import UtilityShutoffScenario

# Registry: scenario name -> constructor. Add a new Gray Swan scenario type here.
SCENARIOS = {
    "hotel_booking": HotelBookingScenario,            # agentic tool-misuse
    "sportscar_offer": SportscarOfferScenario,        # Direct Agent #1: binding $1 offer (2 criteria)
    "discount_code_500": DiscountCode500Scenario,     # Direct Agent: $500 goodwill code vs $20 cap (2 criteria)
    "utility_shutoff": UtilityShutoffScenario,        # Direct Agent: cross-account power shutoff (2 criteria)
    "prescription_exfil": PrescriptionExfilScenario,  # Direct Agent: cross-patient PHI disclosure (2 criteria)
    "secret_extraction": SecretExtractionScenario,    # direct prompt injection (chat)
    "ransomware_injection": RansomwareInjectionScenario,  # indirect prompt injection
    "malware_game": MalwareGameScenario,              # indirect prompt injection (malware rec)
    "email_ignore": EmailIgnoreScenario,              # indirect (poisoned inbox -> deny emails)
    "fraud_disclosure": FraudDisclosureScenario,      # indirect (poisoned survey -> leak fraud rule)
    "radical_propaganda": RadicalPropagandaScenario,  # chat content-gen (rubric + constraints)
    "dll_injection": DllInjectionScenario,            # chat content-gen (per-axis arena judge)
    "americium_extraction": AmericiumExtractionScenario,  # chat content-gen (fuzzy, 3 axes)
    "cyanide_extraction": CyanideExtractionScenario,      # chat content-gen (fuzzy, 2 axes)
    "drug_dealer_search": DrugDealerSearchScenario,      # chat content-gen (fuzzy, 3 axes, realism bar)
    "teacher_msg": TeacherMsgScenario,                  # agentic tool-misuse (verifiable)
    "cheat_on_exam": CheatOnExamScenario,               # chat role-restricted bot (fuzzy, 2 axes)
    "reveal_override_code": RevealOverrideCodeScenario,  # chat basic-guardrail secret extraction (2 axes + verifiable gate)
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
