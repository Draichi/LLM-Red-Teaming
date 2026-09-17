"""Proxy calibration: which local model best predicts the arena?

You develop vectors against a local proxy, but a proxy is only useful if its
break/resist behaviour tracks the real (manual) arena. Once you have arena
outcomes for a handful of payloads, this measures each candidate proxy against
that ground truth and ranks them by rank-correlation -- the analog of Phase-1
judge calibration, but for the target proxy.

Ground truth file (JSONL, gitignored -- it references arena outcomes):
  {"name": "dormant", "payload": "<the injected payload text>", "arena_rate": 0.23}
`arena_rate` is breaks/total on the arena (e.g. 3/13 = 0.23).

For each candidate model, each payload is replayed `trials` times through the
scenario's verifiable judge -> a local break rate. The proxy whose local rates
best correlate (Spearman) with the arena rates across payloads is the best proxy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mta.config import Config
from mta.eval.bench import normalize_model
from mta.targets.agentic import AgenticTarget


def load_truth(path: str | Path) -> list[dict]:
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    for r in rows:
        if "payload" not in r or "arena_rate" not in r:
            raise ValueError("each truth row needs 'payload' and 'arena_rate'")
    return rows


def _ranks(xs: list[float]) -> list[float]:
    """Fractional ranks (ties averaged)."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float:
    """Spearman rank correlation. Returns 0.0 if undefined (constant input)."""
    if len(a) < 2:
        return 0.0
    ra, rb = _ranks(a), _ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    return num / (da * db) if da and db else 0.0


@dataclass
class ProxyResult:
    scenario: str
    payload_names: list[str]
    arena_rates: list[float]
    local_rates: dict[str, list[float]]  # model -> per-payload local break rate

    def ranked(self) -> list[tuple[str, float]]:
        out = [(m, spearman(rates, self.arena_rates)) for m, rates in self.local_rates.items()]
        return sorted(out, key=lambda x: x[1], reverse=True)

    def markdown(self) -> str:
        lines = [f"# Proxy calibration: {self.scenario}", "",
                 f"{len(self.payload_names)} arena-labelled payload(s). Each proxy's local "
                 "break-rate vs the arena rate; ranked by Spearman correlation "
                 "(1.0 = perfectly tracks the arena).", "",
                 "| Proxy | Spearman vs arena | " +
                 " | ".join(n[:10] for n in self.payload_names) + " |",
                 "|---|---|" + "---|" * len(self.payload_names)]
        lines.append("| **arena (truth)** | — | " +
                     " | ".join(f"{r:.2f}" for r in self.arena_rates) + " |")
        for model, corr in self.ranked():
            rates = self.local_rates[model]
            lines.append(f"| `{model.split('/')[-1]}` | **{corr:+.2f}** | " +
                         " | ".join(f"{r:.2f}" for r in rates) + " |")
        best = self.ranked()[0] if self.local_rates else None
        if best:
            lines += ["", f"**Best proxy: `{best[0].split('/')[-1]}`** "
                      f"(Spearman {best[1]:+.2f}) -- develop vectors against this one."]
        return "\n".join(lines)


async def run_proxy_eval(cfg: Config, scenario, truth: list[dict], models: list[str],
                         trials: int = 5) -> ProxyResult:
    import asyncio

    names = [r.get("name", f"p{i}") for i, r in enumerate(truth)]
    arena = [float(r["arena_rate"]) for r in truth]
    payloads = [r["payload"] for r in truth]
    local: dict[str, list[float]] = {}

    for raw in models:
        model = normalize_model(raw)
        mcfg = cfg.model_copy(deep=True)
        mcfg.target.model = model
        target = AgenticTarget(mcfg.target, scenario)

        async def rate(payload: str) -> float:
            breaks = ok = 0
            for _ in range(trials):
                try:
                    result = await target(scenario.assemble(payload))
                    ok += 1
                    breaks += 1 if scenario.judge_injection(result.text, payload).solved else 0
                except Exception:  # noqa: BLE001
                    pass
            return breaks / ok if ok else 0.0

        local[model] = list(await asyncio.gather(*(rate(p) for p in payloads)))
    return ProxyResult(scenario.name, names, arena, local)


def write_report(result: ProxyResult, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"proxy_eval_{result.scenario}.md"
    out.write_text(result.markdown())
    return out
