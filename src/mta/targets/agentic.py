"""Agentic tool-calling target via PROMPTED tool calling.

Native function-calling isn't reliably available on Featherless (a given model's
vLLM deployment may not have `--enable-auto-tool-choice` set), and the whole
point is to attack a wide model zoo. So we describe the scenario's tools in the
system prompt and parse the model's tool calls out of its text -- model-agnostic,
works on any chat model, and never passes `tools=` to litellm (sidestepping the
provider's tool-param handling entirely).

One `__call__` runs the target's response to the latest user turn through the
mini agent loop against the scenario's simulated environment, and returns a
TurnResult with the ORDERED tool-call trace the verifiable judge inspects.
"""

from __future__ import annotations

import asyncio
import json

from mta.config import TargetConfig
from mta.providers import extract_json_object, thinking_off_extra_body
from mta.scenarios.base import Scenario, ToolCall, TurnResult


def _tool_instructions(tools: list[dict]) -> str:
    lines = ["", "You have access to these tools:"]
    for t in tools:
        fn = t.get("function", t)
        params = fn.get("parameters", {}).get("properties", {})
        arg_list = ", ".join(params.keys()) or "(none)"
        lines.append(f"- {fn['name']}({arg_list}): {fn.get('description', '')}")
    lines += [
        "",
        'To call a tool, reply with ONLY a JSON object and nothing else:',
        '{"tool": "<tool_name>", "arguments": {"<arg>": "<value>"}}',
        "After you receive the tool result, either call another tool (same JSON "
        "format) or give your final natural-language reply to the guest. Only "
        "emit the JSON when you actually intend to call a tool.",
    ]
    return "\n".join(lines)


class AgenticTarget:
    def __init__(self, cfg: TargetConfig, scenario: Scenario, max_tool_steps: int = 6, max_retries: int = 4):
        self.cfg = cfg
        self.scenario = scenario
        self.max_tool_steps = max_tool_steps
        self.max_retries = max_retries
        self._sem = asyncio.Semaphore(cfg.max_concurrency)
        import litellm

        self._litellm = litellm

    # Permanent client errors (gated model, bad request, auth, not found) -- no
    # point retrying these; fail fast so a cross-model sweep skips the model.
    _PERMANENT = {"BadRequestError", "AuthenticationError", "NotFoundError",
                  "PermissionDeniedError", "UnsupportedParamsError"}

    _reported_fail = False

    async def _complete(self, **kwargs):
        """acompletion with backoff on transient errors (rate limits). Fails SOFT:
        after retries (or on a permanent error) it returns None instead of raising,
        so one bad call can't crash a long multi-turn/multi-model run -- the caller
        treats a missing response as an empty (non-delivering) turn."""
        last = None
        for attempt in range(self.max_retries):
            try:
                from mta.ledger import ledger_span
                with ledger_span("target"):
                    return await self._litellm.acompletion(**kwargs)
            except Exception as e:  # noqa: BLE001
                last = e
                if type(e).__name__ in self._PERMANENT:
                    break
                await asyncio.sleep(min(2**attempt, 15))
        if not AgenticTarget._reported_fail:
            AgenticTarget._reported_fail = True
            print(f"[target] a call failed (continuing with empty turns): "
                  f"{type(last).__name__}: {last}", file=__import__('sys').stderr)
        return None

    async def __call__(self, messages: list[dict]) -> TurnResult:
        tools = self.scenario.tools()
        if not tools:
            return await self._chat_turn(messages)
        system = self.scenario.system_prompt() + "\n" + _tool_instructions(tools)
        convo = [{"role": "system", "content": system}, *messages]
        start = len(convo)  # everything appended past here is this turn's target-side msgs
        trace: list[ToolCall] = []
        state: dict = {}
        last_text = ""
        finish_reason = ""

        extra = {}
        if getattr(self.cfg, "disable_thinking", False):
            extra["extra_body"] = thinking_off_extra_body()

        async with self._sem:
            for _ in range(self.max_tool_steps):
                resp = await self._complete(
                    model=self.cfg.model,
                    temperature=self.cfg.temperature,
                    max_tokens=self.cfg.max_tokens,
                    messages=convo,
                    **extra,
                )
                if resp is None:
                    break  # failed call -> stop this turn with what we have
                finish_reason = getattr(resp.choices[0], "finish_reason", "") or ""
                text = (resp.choices[0].message.content or "").strip()
                call = _parse_tool_call(text)
                if call is None:
                    last_text = text or last_text
                    break
                trace.append(call)
                result = self.scenario.run_tool(call, state)
                convo.append({"role": "assistant", "content": text})
                convo.append({"role": "user", "content": f"[tool result for {call.name}]: {result}"})

        if last_text:
            convo.append({"role": "assistant", "content": last_text})
        return TurnResult(text=last_text, tool_calls=trace, messages=convo[start:],
                          finish_reason=finish_reason)


    async def _chat_turn(self, messages: list[dict]) -> TurnResult:
        """No-tools scenario (e.g. prompt-injection): plain chat, no tool loop."""
        convo = [{"role": "system", "content": self.scenario.system_prompt()}, *messages]
        extra = {}
        if getattr(self.cfg, "disable_thinking", False):
            extra["extra_body"] = thinking_off_extra_body()
        async with self._sem:
            resp = await self._complete(
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                max_tokens=self.cfg.max_tokens,
                messages=convo,
                **extra,
            )
        text = ((resp.choices[0].message.content if resp else "") or "").strip()
        finish_reason = (getattr(resp.choices[0], "finish_reason", "") or "") if resp else ""
        return TurnResult(text=text, tool_calls=[],
                          messages=[{"role": "assistant", "content": text}],
                          finish_reason=finish_reason)


def _parse_tool_call(text: str) -> ToolCall | None:
    """Return a ToolCall if the reply is a tool-call JSON, else None."""
    try:
        obj = extract_json_object(text)
    except Exception:
        return None
    name = obj.get("tool") or obj.get("name")
    if not name or not isinstance(name, str):
        return None
    args = obj.get("arguments") or obj.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    return ToolCall(name=name, arguments=args)
