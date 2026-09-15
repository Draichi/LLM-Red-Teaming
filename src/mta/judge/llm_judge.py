"""The expensive path: an async LLM judge returning a validated JudgeVerdict.

Uses litellm so the judge and the targets can be any provider behind one call.
Structured output is requested via `response_format=JudgeVerdict` (litellm maps
this to the provider's JSON-schema / tool mechanism). We still parse and
re-validate defensively, because not every routed model honors the schema, and
we always re-derive `score` in code so the model can never hand us a success
number directly.
"""

from __future__ import annotations

import asyncio
import json

from mta.config import JudgeConfig
from mta.judge.rubric import RUBRIC, SYSTEM_PROMPT, JudgeVerdict, derive_score


def format_transcript(messages: list[dict]) -> str:
    """Render a message list as a readable transcript for the judge."""
    lines = []
    for m in messages:
        role = m.get("role", "?").upper()
        lines.append(f"[{role}] {m.get('content', '')}")
    return "\n".join(lines)


class LLMJudge:
    def __init__(self, cfg: JudgeConfig, budget=None):
        self.cfg = cfg
        self.budget = budget  # optional mta.search.budget.Budget for accounting
        self._sem = asyncio.Semaphore(cfg.max_concurrency)
        # Imported lazily so the package imports without the `judge` extra.
        import litellm

        self._litellm = litellm

    async def score_transcript(
        self, objective: str, messages: list[dict]
    ) -> JudgeVerdict:
        """Score a full transcript. `score` is derived in code, not trusted."""
        user = RUBRIC.format(objective=objective, transcript=format_transcript(messages))
        verdict = await self._call(user)
        verdict.score = derive_score(verdict)
        if self.budget is not None:
            self.budget.record_judge_call()
        return verdict

    async def _call(self, user_message: str) -> JudgeVerdict:
        async with self._sem:
            last_err: Exception | None = None
            for attempt in range(self.cfg.max_retries):
                try:
                    resp = await self._litellm.acompletion(
                        model=self.cfg.model,
                        temperature=self.cfg.temperature,
                        max_tokens=self.cfg.max_tokens,
                        response_format=JudgeVerdict,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                    )
                    content = resp.choices[0].message.content
                    return JudgeVerdict.model_validate(_loads(content))
                except Exception as e:  # noqa: BLE001 - retry any transient/parse error
                    last_err = e
                    await asyncio.sleep(min(2**attempt, 8))
            raise RuntimeError(
                f"judge failed after {self.cfg.max_retries} attempts: {last_err}"
            )


def _loads(content: str | dict) -> dict:
    """litellm may hand back a JSON string or an already-parsed dict."""
    if isinstance(content, dict):
        return content
    return json.loads(content)
