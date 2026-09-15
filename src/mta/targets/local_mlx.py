"""Local MLX target: a 7-8B 4-bit open-weight model for free iteration on Apple
silicon. mlx-lm generation is synchronous, so calls run in a thread to keep the
search's async concurrency intact.

Requires the `local` extra (`mlx-lm`). Model is loaded once and reused.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache

from mta.config import TargetConfig


@lru_cache(maxsize=2)
def _load(model_id: str):
    from mlx_lm import load

    return load(model_id)


class LocalMLXTarget:
    def __init__(self, cfg: TargetConfig):
        self.cfg = cfg
        # local generation is single-stream; serialize to one at a time
        self._sem = asyncio.Semaphore(1)

    async def __call__(self, messages: list[dict]) -> str:
        async with self._sem:
            return await asyncio.to_thread(self._generate, messages)

    def _generate(self, messages: list[dict]) -> str:
        from mlx_lm import generate

        model, tokenizer = _load(self.cfg.model)
        prompt = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        return generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=self.cfg.max_tokens,
            verbose=False,
        )
