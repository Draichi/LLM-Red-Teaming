"""Per-call spend & latency ledger (SQLite, stdlib only).

The operator sees OpenRouter traces in Arize, but attacker calls go to
Featherless and never show there, and traces carry no scenario/component
context. This ledger logs EVERY litellm completion at the application level:
model, component (target/attacker/judge/gate/fact_check), scenario, tokens,
latency, status. Costs are computed at report time from the config price
table (flat per-call estimates) alongside the raw tokens, which are the
primary truth for reconciling against provider dashboards.

Enable once at CLI start (`enable_ledger`, called from mta.cli.main); a
litellm CustomLogger callback writes rows from the event loop. The offline
test suite never enables it. The ledger must never break a run: every hook
path is wrapped and registration failures print a warning and continue.
"""

from __future__ import annotations

import contextvars
import sqlite3
import time
from pathlib import Path

DB_PATH = Path("data/ledger.db")

_component: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ledger_component", default="unknown")
_scenario: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ledger_scenario", default="")


class ledger_span:
    """Mark the component for every litellm call inside the block."""

    def __init__(self, component: str):
        self._component = component

    def __enter__(self):
        self._token = _component.set(self._component)

    def __exit__(self, *exc):
        _component.reset(self._token)


def set_scenario(name: str) -> None:
    _scenario.set(name)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    scenario TEXT NOT NULL DEFAULT '',
    component TEXT NOT NULL DEFAULT 'unknown',
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    latency_s REAL,
    status TEXT NOT NULL DEFAULT 'ok'
);
CREATE INDEX IF NOT EXISTS idx_calls_ts ON calls(ts);
CREATE INDEX IF NOT EXISTS idx_calls_scenario ON calls(scenario);
CREATE INDEX IF NOT EXISTS idx_calls_model ON calls(model);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    return conn


def record_call(*, model: str, prompt_tokens: int = 0,
                completion_tokens: int = 0, latency_s: float | None = None,
                status: str = "ok", component: str | None = None,
                scenario: str | None = None,
                db_path: Path = DB_PATH) -> None:
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT INTO calls (ts, scenario, component, model, prompt_tokens,"
            " completion_tokens, latency_s, status) VALUES (?,?,?,?,?,?,?,?)",
            (time.time(),
             _scenario.get() if scenario is None else scenario,
             _component.get() if component is None else component,
             model, prompt_tokens, completion_tokens, latency_s, status))
        conn.commit()
    finally:
        conn.close()


class LedgerLogger:
    """litellm CustomLogger writing one row per completion. Defensive about
    litellm's callback signature drift: everything is getattr-guarded, and any
    internal error is swallowed (the ledger must never break a run)."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        try:  # subclass when available; standalone otherwise
            from litellm.integrations.custom_logger import CustomLogger

            self.__class__ = type("LedgerLogger", (LedgerLogger, CustomLogger), {})
        except Exception:
            pass

    @staticmethod
    def _usage(response_obj) -> tuple[int, int]:
        usage = getattr(response_obj, "usage", None)
        pt = getattr(usage, "prompt_tokens", None) or 0
        ct = getattr(usage, "completion_tokens", None) or 0
        return int(pt), int(ct)

    @staticmethod
    def _latency(start_time, end_time) -> float | None:
        try:
            if start_time and end_time:
                return round((end_time - start_time).total_seconds(), 3)
        except Exception:
            pass
        return None

    def _write(self, kwargs, response_obj, start_time, end_time, status: str):
        try:
            model = str(kwargs.get("model") or "?")
            pt, ct = (0, 0)
            if response_obj is not None:
                pt, ct = self._usage(response_obj)
            record_call(model=model, prompt_tokens=pt, completion_tokens=ct,
                        latency_s=self._latency(start_time, end_time),
                        status=status, db_path=self.db_path)
        except Exception:
            pass

    async def async_log_success_event(self, kwargs, response_obj, start_time,
                                      end_time, **rest):
        self._write(kwargs, response_obj, start_time, end_time, "ok")

    async def async_log_failure_event(self, kwargs, response_obj, start_time,
                                      end_time, **rest):
        self._write(kwargs, response_obj, start_time, end_time, "error")

    # sync fallbacks (older litellm paths call these)
    def log_success_event(self, kwargs, response_obj, start_time, end_time, **rest):
        self._write(kwargs, response_obj, start_time, end_time, "ok")

    def log_failure_event(self, kwargs, response_obj, start_time, end_time, **rest):
        self._write(kwargs, response_obj, start_time, end_time, "error")


_enabled = False


def enable_ledger(db_path: Path = DB_PATH) -> None:
    """Register the global callback. Idempotent; failure warns, never raises."""
    global _enabled
    if _enabled:
        return
    _enabled = True
    try:
        import litellm

        logger = LedgerLogger(db_path)
        callbacks = getattr(litellm, "callbacks", None)
        if isinstance(callbacks, list):
            callbacks.append(logger)
        else:
            litellm.callbacks = [logger]
        connect(db_path).close()  # create schema up front
    except Exception as e:  # noqa: BLE001
        import sys

        print(f"[ledger] failed to enable ({type(e).__name__}: {e}); "
              f"spend tracking off for this run", file=sys.stderr)


def _fold(rows, key_fields: list[str]) -> dict:
    out: dict = {}
    for row in rows:
        key = tuple(row[k] for k in key_fields)
        a = out.setdefault(key, {"calls": 0, "pt": 0, "ct": 0, "errors": 0,
                                 "lat": 0.0, "lat_n": 0})
        a["calls"] += 1
        a["pt"] += row["prompt_tokens"]
        a["ct"] += row["completion_tokens"]
        a["errors"] += 1 if row["status"] != "ok" else 0
        if row["latency_s"] is not None:
            a["lat"] += row["latency_s"]
            a["lat_n"] += 1
    return out


def spend_markdown(db_path: Path = DB_PATH, prices: dict | None = None) -> str:
    """Aggregate the ledger: totals, by component, by model (with the config's
    flat per-call price estimate alongside the raw token truth)."""
    db_path = Path(db_path)
    if not db_path.exists():
        return ("# Spend\n\nNo ledger yet. Runs log every litellm call to "
                "`data/ledger.db` once the ledger is enabled at CLI start.\n")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute("SELECT * FROM calls")]
    finally:
        conn.close()

    prices = prices or {}

    def _usd(models: set[str], calls: int) -> str:
        est = sum(prices.get(m, 0.0) for m in models)  # sum of per-model flat rates x their calls is done by caller
        return f"{est:.4f}" if est else "—"

    lines = ["# Spend", "",
             f"{len(rows)} call(s) logged. USD = flat per-call estimate from the "
             "config `prices` table; tokens are the raw provider-reported truth.",
             ""]

    def _table(title: str, keys: list[str], folded: dict):
        lines.extend([f"## {title}", "",
                      "| " + " | ".join(keys + ["calls", "errors", "prompt tok",
                                                "compl tok", "mean lat (s)",
                                                "USD est"]) + " |",
                      "|" + "---|" * (len(keys) + 5)])
        for key in sorted(folded):
            a = folded[key]
            mean = a["lat"] / a["lat_n"] if a["lat_n"] else None
            key_models = {key[keys.index("model")]} if "model" in keys else set()
            usd = sum(prices.get(m, 0.0) for m in key_models) * a["calls"]
            usd_txt = f"{usd:.4f}" if usd else "—"
            lines.append("| " + " | ".join(str(k) for k in key) +
                         f" | {a['calls']} | {a['errors']} | {a['pt']} | {a['ct']} "
                         f"| {mean:.2f} | {usd_txt} |")

    total_models = {r["model"] for r in rows}
    _table("By scenario x component", ["scenario", "component"],
           _fold(rows, ["scenario", "component"]))
    _table("By model", ["model"], _fold(rows, ["model"]))
    tot = _fold(rows, [])[()] if rows else None
    if tot:
        mean = tot["lat"] / tot["lat_n"] if tot["lat_n"] else 0.0
        usd = sum(
            sum(prices.get(r["model"], 0.0) for r in rows
                if r["model"] == m)
            for m in total_models)
        lines += ["", "## TOTAL", "",
                  f"calls {tot['calls']} | errors {tot['errors']} | prompt tok "
                  f"{tot['pt']} | compl tok {tot['ct']} | mean lat {mean:.2f}s "
                  f"| USD est {usd:.4f}"]
    return "\n".join(lines) + "\n"
