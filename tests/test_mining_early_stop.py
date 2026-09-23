"""Early-stop rule for stochastic mining (`--runs N`): after a run finishes, if
nothing moved (not solved AND every candidate scored 0.0) the beam had no
gradient to climb -- a second stochastic run of the same family against the
same target is expected to repeat it (observed 2026-09-23 on drug_dealer_search:
18 sequential runs, all scores 0.0, judge never even reached). Stop and say so
instead of paying for the remaining run(s)."""

from mta.cli import run_had_no_gradient


def test_solved_run_has_gradient():
    assert run_had_no_gradient(solved=True, cand_scores=[0.0, 0.0]) is False


def test_nonzero_candidate_score_is_gradient():
    # a near-miss (e.g. deflection capped at 0.4) still points somewhere
    assert run_had_no_gradient(solved=False, cand_scores=[0.0, 0.4]) is False


def test_all_zero_unsolved_run_is_flat():
    # the drug_dealer_search 2026-09-23 shape: 21 candidates, every score 0.0
    assert run_had_no_gradient(solved=False, cand_scores=[0.0, 0.0, 0.0]) is True


def test_run_with_no_recorded_candidates_is_flat():
    # every branch died before a candidate was recorded -- nothing to climb on
    assert run_had_no_gradient(solved=False, cand_scores=[]) is True