"""API target via litellm. Used as the held-in overfitting check and, if the
local model turns out too weak to be interesting, as the dev target."""

from __future__ import annotations

import asyncio

from mta.config import TargetConfig


class ApiTarget:
    def __init__(self, cfg: TargetConfig):
        self.cfg = cfg
        self._sem = asyncio.Semaphore(cfg.max_concurrency)
        import litellm

        self._litellm = litellm

    async def __call__(self, messages: list[dict]) -> str:
        kwargs: dict = dict(
            model=self.cfg.model,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            messages=messages,
        )
        if getattr(self.cfg, "disable_thinking", False):
            from mta.providers import thinking_off_extra_body

            kwargs["extra_body"] = thinking_off_extra_body()
        async with self._sem:
            resp = await self._litellm.acompletion(**kwargs)
        return resp.choices[0].message.content or ""

    async def call_with_meta(self, messages: list[dict]) -> tuple[str, str]:
        """Same call, but also returns finish_reason (drives truncation detection
        in the death classifier)."""
        kwargs: dict = dict(
            model=self.cfg.model,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            messages=messages,
        )
        if getattr(self.cfg, "disable_thinking", False):
            from mta.providers import thinking_off_extra_body

            kwargs["extra_body"] = thinking_off_extra_body()
        async with self._sem:
            resp = await self._litellm.acompletion(**kwargs)
        choice = resp.choices[0]
        return (choice.message.content or "", getattr(choice, "finish_reason", "") or "")
