import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from logic import (  # noqa: E402
    calc_ready,
    calc_reduction,
    matrix_hint,
    phase_label,
)


def make_answers(values):
    return {f"q{idx}": value for idx, value in enumerate(values, start=1)}


def test_calc_ready_rounds_average():
    answers = make_answers([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    assert calc_ready(answers) == 55


def test_calc_ready_requires_ten_answers():
    answers = make_answers([0] * 9)
    with pytest.raises(ValueError):
        calc_ready(answers)


def test_calc_reduction_matches_spec_example():
    ready = 68
    adoption = 45
    reduction = calc_reduction(ready, adoption)
    assert math.isclose(reduction, 42.84, rel_tol=1e-3)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "🌱"),
        (39, "🌱"),
        (40, "🔧"),
        (69, "🔧"),
        (70, "🚀"),
        (100, "🚀"),
        (-1, "❓"),
        (101, "❓"),
    ],
)
def test_phase_label_boundaries(score, expected):
    assert phase_label(score) == expected


@pytest.mark.parametrize(
    ("ready", "adoption", "text_snippet"),
    [
        (20, 10, "基盤整備"),
        (50, 20, "日報・報告"),
        (75, 50, "全社最適化"),
    ],
)
def test_matrix_hint_returns_expected_snippet(ready, adoption, text_snippet):
    assert text_snippet in matrix_hint(ready, adoption)
