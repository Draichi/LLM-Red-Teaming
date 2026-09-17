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
    # `--config` is accepted both before and after the subcommand. The main
    # parser carries the real default; a SUPPRESS-defaulted copy on each
    # subparser lets the suffix position override without clobbering when absent.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=argparse.SUPPRESS, help="path to a YAML config")

    parser = argparse.ArgumentParser(prog="mta")
    parser.add_argument("--config", default=None, help="path to a YAML config")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calibrate", parents=[common], help="Phase 1: judge calibration + gate")
    sub.add_parser("sweep-threshold", parents=[common], help="offline judge-threshold sweep over the last calibration (no API calls)")
    sub.add_parser("report", parents=[common], help="offline: write the final judge_calibration.md from persisted scores")
    p_gate = sub.add_parser("gate-eval", parents=[common], help="Phase 2: validate the classifier gate (blinding rate + judge-call savings)")
    p_gate.add_argument("--sample", type=int, default=200)
    p_ag = sub.add_parser("agentic", parents=[common], help="run an agentic tool-misuse scenario (verifiable judge)")
    p_ag.add_argument("--scenario", default="hotel_booking")
    p_ag.add_argument("--model", default=None, help="override target model (bare org/model = featherless)")
    p_ag.add_argument("--attacker-model", default=None, help="override attacker model (use an uninhibited model so it crafts attacks)")
    p_ag.add_argument("--attempts", type=int, default=7, help="single-turn: number of one-shot attacks")
    p_ag.add_argument("--depth", type=int, default=1, help=">1 runs the multi-turn beam")
    p_ag.add_argument("--beam", type=int, default=3, help="beam width (multi-turn)")
    p_ag.add_argument("--proposals", type=int, default=2, help="proposals per beam (multi-turn)")
    p_ag.add_argument("--runs", type=int, default=1, help="run the beam N times (stochastic) to mine several vectors")
    p_ref = sub.add_parser("refine", parents=[common], help="feedback-driven payload refinement -> validated vector library")
    p_ref.add_argument("--scenario", default="ransomware_injection")
    p_ref.add_argument("--model", default=None, help="override target model")
    p_ref.add_argument("--attacker-model", default=None, help="override attacker model")
    p_ref.add_argument("--rounds", type=int, default=4)
    p_ref.add_argument("--beam", type=int, default=3)
    p_ref.add_argument("--proposals", type=int, default=3)
    p_rep = sub.add_parser("replay-vectors", parents=[common], help="replay the vector library across models -> transfer matrix")
    p_rep.add_argument("--scenario", default="ransomware_injection")
    p_rep.add_argument("--models", required=True, help="comma-separated target models")
    p_rep.add_argument("--limit", type=int, default=None, help="only the N most recent vectors")
    p_rep.add_argument("--trials", type=int, default=1, help="run each cell N times -> reliability (breaks/trials)")
    p_sw = sub.add_parser("sweep-models", parents=[common], help="run the same generated attacks across models -> susceptibility matrix")
    p_sw.add_argument("--scenario", default="ransomware_injection")
    p_sw.add_argument("--models", required=True, help="comma-separated target models")
    p_sw.add_argument("--attacks", type=int, default=8, help="number of attacks to generate once and reuse")
    p_pick = sub.add_parser("pick-vector", parents=[common], help="extract a saved vector's turns to a file (for arena submission / --prev-file)")
    p_pick.add_argument("--scenario", required=True)
    p_pick.add_argument("--index", type=int, default=-1, help="which entry (-1 = newest; with --last-batch, 0-based within that batch)")
    p_pick.add_argument("--source", choices=["vectors", "refine"], default="vectors",
                        help="vectors = the library (multi-turn); refine = a refine-manual variant")
    p_pick.add_argument("--last-batch", action="store_true",
                        help="restrict to the most recent run's entries (same timestamp), so --index is stable")
    p_pick.add_argument("--list", action="store_true", help="list the entries (with indices) instead of extracting")
    p_pick.add_argument("--out", default=None, help="write to this file (default: print)")
    p_rm = sub.add_parser("refine-manual", parents=[common], help="refine an attack using the REAL arena's response (human-in-the-loop)")
    p_rm.add_argument("--scenario", required=True)
    p_rm.add_argument("--response-file", required=True, help="text file with the arena model's actual response")
    p_rm.add_argument("--prev-file", default=None, help="text file with the attack you submitted (default: last saved vector)")
    p_rm.add_argument("--note", default="", help="what happened / what to fix (you are the oracle)")
    p_rm.add_argument("--attacker-model", default=None)
    p_rm.add_argument("--proposals", type=int, default=3)
    p_bench = sub.add_parser("bench", parents=[common], help="headline: single-turn vs multi-turn across target models")
    p_bench.add_argument("--scenario", default="hotel_booking")
    p_bench.add_argument("--models", required=True, help="comma-separated target model ids (bare org/model = featherless)")
    p_bench.add_argument("--attempts", type=int, default=7)
    p_bench.add_argument("--depth", type=int, default=2)
    p_bench.add_argument("--beam", type=int, default=3)
    p_bench.add_argument("--proposals", type=int, default=2)
    sub.add_parser("single", parents=[common], help="Phase 3: single-turn ASR baseline")
    sub.add_parser("eval", parents=[common], help="Phase 4: beam-search loop")
    p_human = sub.add_parser("human", parents=[common], help="Phase 5: human baseline session")
    p_human.add_argument("--out", default="data/runs/human.jsonl")
    p_human.add_argument("--sample", type=int, default=20)
    p_fetch = sub.add_parser("fetch-data", parents=[common], help="download calibration data")
    p_fetch.add_argument(
        "--dataset", default="harmbench_val", choices=["harmbench_val"]
    )

    args = parser.parse_args(argv)
    cfg = Config.load(args.config)

    if args.cmd == "calibrate":
        return _calibrate(cfg)
    if args.cmd == "sweep-threshold":
        return _sweep(cfg)
    if args.cmd == "report":
        return _report(cfg)
    if args.cmd == "gate-eval":
        return _gate_eval(cfg, args.sample)
    if args.cmd == "agentic":
        return _agentic(cfg, args)
    if args.cmd == "refine":
        return _refine(cfg, args)
    if args.cmd == "pick-vector":
        return _pick_vector(cfg, args)
    if args.cmd == "refine-manual":
        return _refine_manual(cfg, args)
    if args.cmd == "replay-vectors":
        return _replay(cfg, args)
    if args.cmd == "sweep-models":
        return _sweep_models(cfg, args)
    if args.cmd == "bench":
        return _bench(cfg, args)
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


def _sweep(cfg: Config) -> int:
    from mta.judge.calibrate import best_threshold, sweep_thresholds

    rows = sweep_thresholds(cfg)
    print(f"{'thr':>6} {'kappa':>7} {'fpr':>6} {'fnr':>6} {'acc':>6}  TP/FP/TN/FN  gate")
    for r in rows:
        flag = "PASS" if r["passed"] else ""
        print(f"{r['threshold']:>6.3f} {r['kappa']:>7.3f} {r['fpr']:>6.3f} "
              f"{r['fnr']:>6.3f} {r['accuracy']:>6.3f}  "
              f"{r['tp']}/{r['fp']}/{r['tn']}/{r['fn']}  {flag}")
    best = best_threshold(rows)
    if best:
        print(f"\nbest: threshold={best['threshold']:.3f} "
              f"kappa={best['kappa']:.3f} fpr={best['fpr']:.3f} "
              f"-> {'PASS' if best['passed'] else 'still FAIL'}")
        print(f"(set judge.success_threshold={best['threshold']:.3f} in your config)")
    return 0


def _report(cfg: Config) -> int:
    from mta.judge.calibrate import finalize_report

    out = finalize_report(cfg)
    print(f"wrote {out}")
    return 0


def _gate_eval(cfg: Config, sample: int) -> int:
    from mta.judge.gate_eval import run_gate_eval

    result = asyncio.run(run_gate_eval(cfg, sample_size=sample))
    print(result.as_text(cfg))
    return 0


def _mine_beam(cfg: Config, scenario, args, runner, file_prefix: str, kind: str,
               needs_review: bool):
    """Run a beam `args.runs` times (stochastic -> different vectors each run),
    saving every solved vector to the library. Returns (runs_solved, vectors_saved)."""
    import json
    from pathlib import Path

    from mta.search.agentic_loop import save_beam_vector

    base_seed = cfg.seed
    n_solved = saved = 0
    for i in range(args.runs):
        cfg.seed = base_seed + i  # vary the attacker's strategy sampling per run
        cand_path = Path(cfg.runs_dir) / f"{file_prefix}_{args.scenario}.jsonl"
        cand_path.parent.mkdir(parents=True, exist_ok=True)
        fh = cand_path.open("w")
        result = asyncio.run(runner(
            cfg, scenario, beam_width=args.beam, depth=args.depth, n_proposals=args.proposals,
            on_candidate=lambda r: (fh.write(json.dumps(r) + "\n"), fh.flush()),
        ))
        fh.close()
        tag = f"[run {i + 1}/{args.runs}] "
        print(tag + result.summary().replace("\n", "\n" + " " * len(tag)))
        if result.solved:
            n_solved += 1
            lib = save_beam_vector(result, cfg.target.model, Path("data/vectors"),
                                   kind=kind, needs_review=needs_review)
            if lib:
                saved += 1
    cfg.seed = base_seed
    return n_solved, saved


def _agentic(cfg: Config, args) -> int:
    from mta.scenarios import get_scenario
    from mta.search.agentic_loop import (
        run_agentic_beam, run_agentic_single, write_attempts,
    )
    from pathlib import Path
    import json

    scenario = get_scenario(args.scenario)
    if getattr(args, "model", None):
        from mta.eval.bench import normalize_model
        cfg.target.model = normalize_model(args.model)
    if getattr(args, "attacker_model", None):
        from mta.eval.bench import normalize_model
        cfg.attacker_model = normalize_model(args.attacker_model)
    if getattr(scenario, "kind", "") == "indirect":
        from mta.search.agentic_loop import (
            run_indirect_injection, save_attempt_vectors, write_attempts,
        )
        result = asyncio.run(run_indirect_injection(cfg, scenario, args.attempts))
        write_attempts(result, Path(cfg.runs_dir) / f"agentic_{args.scenario}.jsonl")
        print(result.summary())
        if result.solved:
            n = save_attempt_vectors(result, cfg.target.model, Path("data/vectors"),
                                     kind="indirect", needs_review=False)
            print(f"{n} solved payload(s) saved to data/vectors/{args.scenario}.jsonl "
                  "(verifiable judge -- trustworthy)")
        return 0 if result.solved else 2
    if getattr(scenario, "kind", "") == "chat_content":
        if args.depth > 1:
            from mta.search.agentic_loop import run_content_beam
            n_solved, saved = _mine_beam(cfg, scenario, args, run_content_beam,
                                         "content_beam", "chat_content", needs_review=True)
            print(f"\n{n_solved}/{args.runs} run(s) solved; {saved} candidate vector(s) saved.")
            print("NOTE: content scenarios are fuzzy-judged (LLM rubric, ~15% FPR). Each "
                  "'solved' is a CANDIDATE -- review the transcript before treating it as a break.")
            return 0 if n_solved else 2
        from mta.search.agentic_loop import run_content_scenario, write_attempts
        result = asyncio.run(run_content_scenario(cfg, scenario, args.attempts))
        write_attempts(result, Path(cfg.runs_dir) / f"agentic_{args.scenario}.jsonl")
        print(result.summary())
        return 0 if result.solved else 2
    if args.depth > 1:
        n_solved, saved = _mine_beam(cfg, scenario, args, run_agentic_beam,
                                     "agentic_beam", "agentic", needs_review=False)
        print(f"\n{n_solved}/{args.runs} run(s) solved; {saved} vector(s) saved "
              "(verifiable judge -- trustworthy).")
        return 0 if n_solved else 2

    result = asyncio.run(run_agentic_single(cfg, scenario, args.attempts))
    write_attempts(result, Path(cfg.runs_dir) / f"agentic_{args.scenario}.jsonl")
    print(result.summary())
    return 0 if result.solved else 2


def _refine(cfg: Config, args) -> int:
    from mta.eval.bench import normalize_model
    from mta.scenarios import get_scenario
    from mta.search.agentic_loop import run_injection_refine, save_vectors
    from pathlib import Path
    import json

    scenario = get_scenario(args.scenario)
    if args.model:
        cfg.target.model = normalize_model(args.model)
    if getattr(args, "attacker_model", None):
        cfg.attacker_model = normalize_model(args.attacker_model)
    cand_path = Path(cfg.runs_dir) / f"refine_{args.scenario}.jsonl"
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    fh = cand_path.open("w")
    result = asyncio.run(run_injection_refine(
        cfg, scenario, rounds=args.rounds, beam_width=args.beam, n_proposals=args.proposals,
        on_candidate=lambda r: (fh.write(json.dumps(r) + "\n"), fh.flush()),
    ))
    fh.close()
    lib = save_vectors(result, Path("data/vectors"))
    print(result.summary())
    if lib:
        print(f"validated vectors appended to: {lib}")
    return 0 if result.solved else 2


def _sweep_models(cfg: Config, args) -> int:
    from mta.eval.replay import run_sweep, write_report
    from mta.scenarios import get_scenario
    from pathlib import Path

    scenario = get_scenario(args.scenario)
    models = [m for m in args.models.split(",") if m.strip()]
    matrix = asyncio.run(run_sweep(cfg, scenario, models, args.attacks))
    out = write_report(matrix, Path(cfg.reports_dir))
    print(matrix.markdown())
    print(f"\nreport: {out}")
    return 0


def _vector_turns(entry: dict) -> list[str]:
    """The ordered attack turns of a library/refine entry (multi-turn vector,
    single-shot payload, or a refine-manual variant)."""
    if entry.get("turns"):
        return list(entry["turns"])
    for k in ("payload", "variant"):
        if entry.get(k):
            return [entry[k]]
    return []


def _pick_vector(cfg: Config, args) -> int:
    import json
    from pathlib import Path

    src = (Path("data/vectors") if args.source == "vectors"
           else Path(cfg.runs_dir)) / (
        f"{args.scenario}.jsonl" if args.source == "vectors"
        else f"refine_manual_{args.scenario}.jsonl")
    if not src.exists():
        print(f"nothing at {src} -- run the beam/refine first.")
        return 1
    rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]

    # --last-batch: keep only the entries from the most recent run (same ts), so
    # --index counts within that batch (0 = first of the batch) instead of over
    # the whole accumulated file.
    if args.last_batch and rows:
        last_ts = rows[-1].get("ts")
        rows = [r for r in rows if r.get("ts") == last_ts]

    if args.list:
        for i, r in enumerate(rows):
            preview = (_vector_turns(r) or [""])[0][:90].replace("\n", " ")
            print(f"[{i}] {preview}")
        print(f"({len(rows)} entries" + (" in last batch)" if args.last_batch else ")"))
        return 0

    try:
        entry = rows[args.index]
    except IndexError:
        print(f"index {args.index} out of range ({len(rows)} entries)")
        return 1

    turns = _vector_turns(entry)
    if not turns:
        print("entry has no turns/payload")
        return 1
    # Number the turns so you can submit them in order in the arena; a single
    # turn is written bare so it drops straight into --prev-file.
    text = turns[0] if len(turns) == 1 else "\n\n".join(
        f"# turn {i}\n{t}" for i, t in enumerate(turns, 1))

    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {len(turns)} turn(s) to {args.out}")
    else:
        print(text)
    return 0


def _refine_manual(cfg: Config, args) -> int:
    from mta.eval.bench import normalize_model
    from mta.eval.replay import load_vectors
    from mta.scenarios import get_scenario
    from mta.search.agentic_loop import run_refine_manual
    from pathlib import Path
    import json
    import time

    scenario = get_scenario(args.scenario)
    if args.attacker_model:
        cfg.attacker_model = normalize_model(args.attacker_model)

    # the attack you submitted: explicit file, else the last saved vector
    if args.prev_file:
        prev = Path(args.prev_file).read_text().strip()
    else:
        vecs = load_vectors(args.scenario, limit=1)
        if not vecs:
            print(f"no --prev-file and no saved vector in data/vectors/{args.scenario}.jsonl")
            return 1
        v = vecs[0]
        prev = (v.get("turns") or [v.get("payload", "")])[-1]
    arena_response = Path(args.response_file).read_text().strip()

    variants = asyncio.run(run_refine_manual(
        cfg, scenario, prev, arena_response, args.note, args.proposals))

    out = Path(cfg.runs_dir) / f"refine_manual_{args.scenario}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as fh:
        for i, variant in enumerate(variants):
            print(f"\n--- refined variant {i} ---\n{variant}")
            fh.write(json.dumps({"scenario": args.scenario, "prev": prev,
                                 "arena_response": arena_response, "note": args.note,
                                 "variant": variant, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
    print(f"\n{len(variants)} refined variant(s) written to {out}. Submit them to the "
          "arena and bring the responses back to refine again.")
    return 0


def _replay(cfg: Config, args) -> int:
    from mta.eval.replay import (
        load_vectors, run_agentic_replay, run_content_replay, run_replay, write_report,
    )
    from mta.scenarios import get_scenario
    from pathlib import Path

    scenario = get_scenario(args.scenario)
    vectors = load_vectors(args.scenario, limit=args.limit)
    if not vectors:
        print(f"no vectors in data/vectors/{args.scenario}.jsonl -- run `mta refine` or the content beam first.")
        return 1
    models = [m for m in args.models.split(",") if m.strip()]
    kind = getattr(scenario, "kind", "")
    if kind == "chat_content":
        matrix = asyncio.run(run_content_replay(cfg, scenario, models, vectors, trials=args.trials))
    elif kind == "agentic":
        matrix = asyncio.run(run_agentic_replay(cfg, scenario, models, vectors, trials=args.trials))
    else:  # single-shot injection (indirect / secret extraction)
        matrix = asyncio.run(run_replay(cfg, scenario, models, vectors, trials=args.trials))
    out = write_report(matrix, Path(cfg.reports_dir))
    print(matrix.markdown())
    print(f"\nreport: {out}")
    return 0


def _bench(cfg: Config, args) -> int:
    from mta.eval.bench import run_bench, write_report
    from mta.scenarios import get_scenario
    from pathlib import Path

    scenario = get_scenario(args.scenario)
    models = [m for m in args.models.split(",") if m.strip()]
    result = asyncio.run(run_bench(
        cfg, scenario, models,
        attempts=args.attempts, depth=args.depth, beam=args.beam, proposals=args.proposals,
    ))
    out = write_report(result, Path(cfg.reports_dir))
    print(result.markdown())
    print(f"\nreport: {out}")
    return 0


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
