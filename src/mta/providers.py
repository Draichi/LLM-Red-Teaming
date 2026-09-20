"""Provider-portability helpers for litellm calls.

The judge, attacker, and targets all route through litellm, but providers differ
in two ways that matter here:

1. **Structured output.** Anthropic / OpenAI honor a JSON *schema*
   (`response_format=<PydanticModel>`). Open-weight providers like Featherless
   serve vLLM and reliably support only JSON *mode*
   (`response_format={"type": "json_object"}`), so we inject the schema into the
   prompt and validate ourselves.

2. **Reasoning toggle.** Reasoning models (Qwen3, GLM, DeepSeek-R1, Kimi-K2-
   Thinking) think by default. On Featherless that is turned off with
   `chat_template_kwargs={"enable_thinking": false}`, passed via litellm's
   `extra_body`. Disabling it is faster and yields clean JSON (no
   `reasoning_content` eating the turn).
"""

from __future__ import annotations

import json
import os
import re

FEATHERLESS_BASE = "https://api.featherless.ai/v1"

# Prefixes treated as already-routed litellm ids (a frontier judge, an OpenRouter
# id, or an id we built); bare `org/model` defaults to Featherless for backward
# compat. OpenRouter (openrouter/<provider>/<model>) carries the frontier proxies
# that best resemble the arena.
_KNOWN_PREFIXES = ("featherless_ai/", "anthropic/", "claude-", "openrouter/")


def normalize_model(m: str) -> str:
    """Bare `org/model` -> a Featherless litellm id; already-routed ids pass."""
    m = m.strip()
    if m.startswith(_KNOWN_PREFIXES):
        return m
    return "featherless_ai/" + m


def openai_compat_route(model: str) -> dict:
    """litellm kwargs to reach a model via the generic OpenAI-compatible provider.

    The `featherless_ai/` provider in litellm hard-rejects `tools`/`tool_choice`
    in its transformation layer, so a tool-calling target can't use it. Featherless
    is OpenAI-compatible, so we route through litellm's `openai/` provider pointed
    at Featherless's endpoint, which forwards tools natively. Non-featherless
    models are returned unchanged."""
    if model.startswith("featherless_ai/"):
        bare = model[len("featherless_ai/"):]
        return {
            "model": "openai/" + bare,
            "api_base": FEATHERLESS_BASE,
            "api_key": os.environ.get("FEATHERLESS_AI_API_KEY"),
        }
    return {"model": model}


def thinking_off_extra_body() -> dict:
    """Body fragment that disables reasoning on vLLM-served models (Featherless).

    Harmless for non-reasoning models (the template kwarg is ignored)."""
    return {"chat_template_kwargs": {"enable_thinking": False}}


def supports_json_schema(model: str) -> bool:
    """True if the provider honors a JSON *schema* response_format."""
    try:
        import litellm

        return bool(litellm.supports_response_schema(model=model))
    except Exception:
        return False


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def extract_json_object(content: str | dict) -> dict:
    """Parse a JSON object from a model reply, tolerating fences and prose.

    Handles: already-parsed dicts, ```json fences, and leading/trailing text
    around a single top-level object. Raises ValueError if no object is found.
    """
    if isinstance(content, dict):
        return content
    text = content.strip()
    text = _FENCE.sub("", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # slice the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
