"""Automated multi-turn jailbreak search + human-baseline benchmark.

Phase 1 (judge calibration) is the gate everything else stands on, so it is the
only fully implemented subsystem: `mta.judge`. The attacker/search/targets
packages ship their interfaces and are filled in Phases 3-4 (see FUTURE.md).
"""

__version__ = "0.1.0"
