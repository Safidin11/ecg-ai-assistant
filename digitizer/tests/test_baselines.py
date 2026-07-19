"""Тесты детекции строк по сигналу и определения формата."""
import numpy as np

from ecg_layout.baselines import (
    detect_n_rows,
    detect_row_bands,
    standard_format_from_rows,
)
from ecg_layout.matching import match_text_to_lead


def _synthetic_rows(n_rows: int, h: int = 1200, w: int = 800):
    """Строит маску чернил с n_rows горизонтальными полосами сигнала.

    Каждая полоса — область умеренной высоты с "чернилами" (имитация кривой,
    занимающей вертикальный диапазон), между полосами — пустое место.
    """
    mask = np.zeros((h, w), dtype=bool)
    hb = max(6, int(0.15 * h / n_rows))  # полувысота полосы
    for i in range(n_rows):
        cy = int((i + 0.5) * h / n_rows)
        mask[cy - hb:cy + hb, ::3] = True  # ~33% чернил в каждой строке полосы
    return mask


def test_detect_row_bands_counts():
    for n in (3, 6, 12):
        mask = _synthetic_rows(n)
        assert detect_n_rows(mask) == n


def test_row_bands_are_ordered_top_to_bottom():
    bands = detect_row_bands(_synthetic_rows(6))
    ys = [y0 for y0, _ in bands]
    assert ys == sorted(ys)


def test_standard_format_from_rows():
    assert standard_format_from_rows(3)["template"] == "standard_3x4"
    assert standard_format_from_rows(4)["template"] == "standard_3x4"
    assert standard_format_from_rows(6)["template"] == "standard_6x2"
    assert standard_format_from_rows(12)["template"] == "standard_12x1"
    # с запасом на погрешность детекции
    assert standard_format_from_rows(10)["template"] == "standard_12x1"
    assert standard_format_from_rows(7)["template"] == "standard_6x2"


def test_matching_two_char_augmented():
    # потеряна первая 'a': VR/VL/VF -> aVR/aVL/aVF
    assert match_text_to_lead("VR")[0] == "aVR"
    assert match_text_to_lead("VF")[0] == "aVF"
    assert match_text_to_lead("VL")[0] == "aVL"
