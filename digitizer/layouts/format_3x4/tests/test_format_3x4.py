"""Быстрые тесты модульной архитектуры и формата 3×4 (без OCR/реальных фото)."""
import numpy as np

from layouts.common.signal import fill_gaps, resample
from layouts.common.tracking import track_curve
from layouts.common.types import DigitizeResult
from layouts.format_3x4.config import CELL_MAP
from layouts.format_3x4.detector import _columns_from_labels, _content_box


def test_cell_map_covers_12_leads():
    assert set(CELL_MAP.values()) == {
        "I", "II", "III", "aVR", "aVL", "aVF",
        "V1", "V2", "V3", "V4", "V5", "V6",
    }


def test_columns_even_split_fallback():
    cols = _columns_from_labels([], 0, 400)     # нет подписей -> 4 равные
    assert len(cols) == 4
    assert cols[0][0] == 0 and cols[-1][1] == 400


def test_content_box_trims_dense_border():
    mask = np.zeros((100, 200), dtype=bool)
    mask[40:42, 10:190] = True                  # тонкая сигнальная линия
    mask[:, 195:200] = True                     # плотная рамка справа
    x0, y0, x1, y1 = _content_box(mask)
    assert x1 <= 195                            # рамка обрезана


def test_signal_helpers():
    assert not np.isnan(fill_gaps(np.array([0.0, np.nan, 2.0]))).any()
    assert len(resample(np.array([0.0, 1.0]), 10)) == 10


def test_track_curve_follows_flat_line():
    mask = np.zeros((60, 100), dtype=bool)
    mask[30, :] = True                          # плоская линия на y=30
    dev = track_curve(mask, (0, 0, 100, 60), baseline=30)
    assert np.allclose(dev, 0.0, atol=1.0)


def test_digitize_result_db_record():
    r = DigitizeResult(np.zeros((12, 5000), np.float32), 500, 25, 10, "3x4", [])
    assert set(r.to_db_record()) == {"signals", "sampling_rate", "speed", "gain", "layout"}
