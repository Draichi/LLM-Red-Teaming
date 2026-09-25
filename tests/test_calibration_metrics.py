"""Tests for the judge-calibration metrics (pure functions, no network)."""

import pytest

from mta.calibration import (
    cohens_kappa,
    floor_confusion,
    mae_points,
    per_axis_report,
    truth_axis_scores,
)


class TestFloorConfusion:
    def test_perfect_agreement(self):
        # local 0-10 scores vs arena 0-100 truth
        local = [10, 10, 0, 0]
        arena = [90, 100, 0, 20]
        cm = floor_confusion(local, arena)
        assert (cm.tp, cm.fp, cm.fn, cm.tn) == (2, 0, 0, 2)

    def test_false_positive(self):
        # local passes an axis the arena failed -> FPR
        cm = floor_confusion([8], [0])
        assert (cm.tp, cm.fp, cm.fn, cm.tn) == (0, 1, 0, 0)

    def test_false_negative(self):
        cm = floor_confusion([2], [90])
        assert (cm.tp, cm.fp, cm.fn, cm.tn) == (0, 0, 1, 0)

    def test_boundary_arena_70_counts_as_pass(self):
        # arena floor semantics: pass at >= 70; local: >= 7 on 0-10
        cm = floor_confusion([7], [70])
        assert cm.tp == 1

    def test_boundary_local_just_below(self):
        cm = floor_confusion([6], [70])
        assert cm.fn == 1


class TestCohensKappa:
    def test_perfect_agreement_is_one(self):
        k = cohens_kappa(tp=3, fp=0, fn=0, tn=3)
        assert k == pytest.approx(1.0)

    def test_chance_agreement_is_near_zero(self):
        # po = pe -> kappa 0: each side passes half, none of it aligned
        k = cohens_kappa(tp=1, fp=1, fn=1, tn=1)
        assert k == pytest.approx(0.0)

    def test_all_false_positive_degenerates_to_zero(self):
        # arena never passes -> marginals degenerate; kappa pins at 0
        assert cohens_kappa(tp=0, fp=4, fn=0, tn=0) == pytest.approx(0.0)

    def test_perfectly_inverted_is_minus_one(self):
        k = cohens_kappa(tp=0, fp=2, fn=2, tn=0)
        assert k == pytest.approx(-1.0)

    def test_empty_table_returns_none(self):
        assert cohens_kappa(tp=0, fp=0, fn=0, tn=0) is None


class TestMae:
    def test_zero_error(self):
        assert mae_points([8, 0], [80, 0]) == pytest.approx(0.0)

    def test_direction_does_not_matter(self):
        assert mae_points([8, 0], [100, 0]) == pytest.approx(10.0)

    def test_average(self):
        assert mae_points([10, 0], [70, 10]) == pytest.approx(20.0)


class TestTruthAxisScores:
    def test_reads_axes_dict(self):
        rec = {"axes": {"ai_origination": 90.0, "answer_revealed": 0.0}}
        assert truth_axis_scores(rec) == {
            "ai_origination": 90.0,
            "answer_revealed": 0.0,
        }

    def test_missing_axes_is_empty(self):
        assert truth_axis_scores({}) == {}


class TestPerAxisReport:
    def test_groups_by_axis(self):
        pairs = [
            ("a", 10, 90),
            ("a", 0, 0),
            ("b", 5, 90),
        ]
        report = per_axis_report(pairs)
        assert set(report) == {"a", "b"}
        assert report["a"]["n"] == 2
        assert report["a"]["confusion"]["fp"] == 0
        assert report["b"]["confusion"]["fn"] == 1
        assert report["b"]["mae"] == pytest.approx(40.0)
