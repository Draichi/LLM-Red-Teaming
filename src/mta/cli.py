"""`mta` command-line entry point.

Subcommands:
  calibrate   Phase 1 gate: run the judge over labeled data, write the report.
  single      Phase 3 floor: single-turn ASR baseline.
  eval        Phase 4: beam-search loop over the objective set.
  human       Phase 5: interactive human-baseline session.
  fetch-data  Download the calibration set(s) into data/calibration/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mta.config import Config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mta")
    parser.add_argument("--config", default=None, help="path to a YAML config")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calibrate", help="Phase 1: judge calibration + gate")
    sub.add_parser("single", help="Phase 3: single-turn ASR baseline")
    sub.add_parser("eval", help="Phase 4: beam-search loop")
    p_human = sub.add_parser("human", help="Phase 5: human baseline session")
    p_human.add_argument("--out", default="data/runs/human.jsonl")
    p_human.add_argument("--sample", type=int, default=20)
    p_fetch = sub.add_parser("fetch-data", help="download calibration data")
    p_fetch.add_argument(
        "--dataset", default="harmbench_val", choices=["harmbench_val"]
    )

    args = parser.parse_args(argv)
    cfg = Config.load(args.config)

    if args.cmd == "calibrate":
        return _calibrate(cfg)
    if args.cmd == "single":
        return _single(cfg)
    if args.cmd == "eval":
        return _eval(cfg)
    if args.cmd == "human":
        return _human(cfg, Path(args.out), args.sample)
    if args.cmd == "fetch-data":
        return _fetch(cfg, args.dataset)
    return 1


def _calibrate(cfg: Config) -> int:
    from mta.judge.calibrate import run_calibration, write_report

    result = asyncio.run(run_calibration(cfg))
    out = write_report(result, cfg)
    print(f"kappa={result.kappa:.3f} fpr={result.false_positive_rate:.3f} "
          f"n={result.n} -> {'PASS' if result.passed else 'FAIL'}")
    print(f"report: {out}")
    return 0 if result.passed else 2


def _single(cfg: Config) -> int:
    from mta.eval.run_loop import asr, load_objectives, run_single_turn

    objs = load_objectives(cfg.behaviors_path)
    results = asyncio.run(run_single_turn(cfg, objs))
    print(f"ASR@1turn = {asr(results):.3f} over {len(results)} objectives")
    return 0


def _eval(cfg: Config) -> int:
    from mta.eval.run_loop import asr, load_objectives, run_beam

    objs = load_objectives(cfg.behaviors_path)
    results = asyncio.run(run_beam(cfg, objs))
    print(f"ASR@{cfg.search.depth}turns = {asr(results):.3f} over {len(results)} objectives")
    return 0


def _human(cfg: Config, out: Path, sample: int) -> int:
    from mta.eval.run_human import run_human_session, summarize_human
    from mta.eval.run_loop import load_objectives

    objs = load_objectives(cfg.behaviors_path)[:sample]
    print("REMINDER: run this BEFORE looking at automated results for these objectives.")
    asyncio.run(run_human_session(cfg, objs, out))
    print(json.dumps(summarize_human(out), indent=2))
    return 0


def _fetch(cfg: Config, dataset: str) -> int:
    from mta.data_fetch import fetch_harmbench_val

    if dataset == "harmbench_val":
        path = fetch_harmbench_val(cfg.calibration.path)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
