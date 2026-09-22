"""Per-call spend ledger: recording, spans, the litellm callback, and the
spend report. Offline (SQLite via stdlib, fake response objects)."""

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

from mta.ledger import (
    LedgerLogger,
    connect,
    ledger_span,
    record_call,
    set_scenario,
    spend_markdown,
)


def test_record_and_aggregate(tmp_path):
    db = tmp_path / "ledger.db"
    record_call(model="mA", prompt_tokens=100, completion_tokens=50,
                latency_s=1.5, db_path=db, component="target", scenario="cyanide")
    record_call(model="mA", prompt_tokens=200, completion_tokens=80,
                latency_s=2.5, db_path=db, component="target", scenario="cyanide")
    record_call(model="mB", prompt_tokens=10, completion_tokens=5,
                latency_s=0.5, status="error", db_path=db,
                component="attacker", scenario="cyanide")
    md = spend_markdown(db, prices={"mA": 0.001, "mB": 0.002})
    assert "cyanide" in md and "target" in md and "attacker" in md
    assert "mA" in md and "mB" in md
    assert "| 2 | 0 | 300 | 130 |" in md        # mA row: calls, errors, pt, ct
    assert "0.0020" in md                        # 2 x mA flat price
    assert "calls 3 | errors 1 |" in md          # total row


def test_spans_and_scenario_contextvars(tmp_path):
    db = tmp_path / "ledger.db"
    with ledger_span("judge"):
        record_call(model="mJ", db_path=db)
    set_scenario("demo")
    with ledger_span("gate"):
        record_call(model="mG", db_path=db)
    conn = connect(db)
    rows = conn.execute("SELECT component, scenario, model FROM calls ORDER BY id").fetchall()
    conn.close()
    assert rows[0] == ("judge", "", "mJ")
    assert rows[1] == ("gate", "demo", "mG")


def test_ledger_logger_success_and_failure(tmp_path):
    db = tmp_path / "ledger.db"
    logger = LedgerLogger(db)
    start = datetime(2026, 9, 21, 12, 0, 0)
    end = start + timedelta(seconds=1.25)
    resp = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=42,
                                                 completion_tokens=24))

    asyncio.run(logger.async_log_success_event(
        {"model": "openai/gpt-x"}, resp, start, end))
    asyncio.run(logger.async_log_failure_event(
        {"model": "featherless/y"}, None, start, end))

    conn = connect(db)
    rows = conn.execute(
        "SELECT model, prompt_tokens, completion_tokens, latency_s, status "
        "FROM calls ORDER BY id").fetchall()
    conn.close()
    assert rows[0] == ("openai/gpt-x", 42, 24, 1.25, "ok")
    assert rows[1][0] == "featherless/y" and rows[1][4] == "error"
    assert rows[1][1] == 0  # no usage object on failures


def test_ledger_logger_never_raises(tmp_path):
    # a pathological kwargs/response must not break the run being logged
    logger = LedgerLogger(tmp_path / "ledger.db")
    asyncio.run(logger.async_log_success_event(None, object(), None, None))
    asyncio.run(logger.async_log_failure_event({"model": 1}, None, "x", "y"))


def test_spend_markdown_empty(tmp_path):
    assert "No ledger yet" in spend_markdown(tmp_path / "nope.db")
