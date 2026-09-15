"""Target protocol: an async callable that maps a message list to a reply.

Keeping the surface this small is what lets the same beam search run against a
local 4-bit model (free iteration) and an API model (overfitting check) with no
change to the search. The Gray Swan held-out target is deliberately NOT a Target
implementation -- submission there is manual, by their rules (see FUTURE.md).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mta.config import TargetConfig


@runtime_checkable
class Target(Protocol):
    async def __call__(self, messages: list[dict]) -> str: ...


def build_target(cfg: TargetConfig) -> Target:
    if cfg.kind == "api":
        from mta.targets.api import ApiTarget

        return ApiTarget(cfg)
    if cfg.kind == "local_mlx":
        from mta.targets.local_mlx import LocalMLXTarget

        return LocalMLXTarget(cfg)
    raise ValueError(f"unknown target kind {cfg.kind!r}")
