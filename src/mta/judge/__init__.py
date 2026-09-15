"""Phase 1: the judge. A value function for beam search, not a report generator.

The judge is worth building only because the search in Phase 4 optimizes against
its score. That is also why it is calibrated against human labels first
(`calibrate.py`) before any search consumes it.
"""

from mta.judge.rubric import JudgeVerdict, derive_score
from mta.judge.llm_judge import LLMJudge

__all__ = ["JudgeVerdict", "derive_score", "LLMJudge"]
