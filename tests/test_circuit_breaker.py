"""Per-provider circuit breaker on the agentic target: after N consecutive
failures a model fails fast instead of burning the full timeout per call."""

import asyncio

from mta.targets.agentic import AgenticTarget


class _FlakyLitellm:
    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    async def acompletion(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("provider down")
        return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}


def _target(litellm):
    t = AgenticTarget.__new__(AgenticTarget)
    t._litellm = litellm
    t.max_retries = 1  # one try per _complete call keeps the test fast
    return t


def test_circuit_opens_after_consecutive_failures():
    AgenticTarget._consecutive_failures.clear()
    fake = _FlakyLitellm(failures=10)
    t = _target(fake)

    async def run():
        for _ in range(3):
            assert await t._complete(model="dead/model") is None
        # circuit now open: further calls fail fast without hitting the provider
        calls_before = fake.calls
        assert await t._complete(model="dead/model") is None
        assert fake.calls == calls_before  # no new provider call

    asyncio.run(run())
    assert AgenticTarget._consecutive_failures["dead/model"] >= 3


def test_success_resets_the_breaker():
    AgenticTarget._consecutive_failures.clear()
    fake = _FlakyLitellm(failures=2)  # fails twice, then recovers
    t = _target(fake)

    async def run():
        assert await t._complete(model="flaky/model") is None
        assert await t._complete(model="flaky/model") is None
        resp = await t._complete(model="flaky/model")
        assert resp is not None
        assert AgenticTarget._consecutive_failures.get("flaky/model", 0) == 0

    asyncio.run(run())
