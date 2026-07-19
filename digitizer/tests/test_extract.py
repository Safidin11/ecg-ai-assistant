"""Тесты извлечения сигнала из нарисованной кривой."""
import numpy as np

from ecg_layout.extract import extract_trace_in_band, fill_gaps, trace_to_signal


def _draw_curve(y_of_x: np.ndarray, h: int, w: int, thickness: int = 2) -> np.ndarray:
    """Рисует кривую (маска чернил): в столбце x чернила вокруг y_of_x[x]."""
    mask = np.zeros((h, w), dtype=bool)
    for x in range(w):
        y = int(round(y_of_x[x]))
        mask[max(0, y - thickness):y + thickness + 1, x] = True
    return mask


def test_extracts_sine_curve():
    h, w = 200, 300
    x = np.arange(w)
    true_y = 100 + 40 * np.sin(2 * np.pi * x / 60)  # синус вокруг y=100
    mask = _draw_curve(true_y, h, w)

    trace = extract_trace_in_band(mask, y_top=0, y_bottom=h)
    # извлечённая кривая близка к исходной (в пределах толщины линии)
    assert np.nanmax(np.abs(trace - true_y)) < 3.0


def test_fill_gaps_interpolates():
    trace = np.array([10.0, np.nan, np.nan, 40.0])
    filled = fill_gaps(trace)
    assert not np.isnan(filled).any()
    assert abs(filled[1] - 20.0) < 1e-6
    assert abs(filled[2] - 30.0) < 1e-6


def test_trace_to_signal_inverts_and_centres():
    # прямая линия -> сигнал около нуля (нет отклонения от изолинии)
    trace = np.full(50, 100.0)
    sig = trace_to_signal(trace)
    assert np.allclose(sig, 0.0)

    # пик ВВЕРХ (меньший Y) -> положительное значение сигнала
    trace2 = np.full(50, 100.0)
    trace2[25] = 60.0  # выше линии на 40 пикселей
    sig2 = trace_to_signal(trace2, baseline=100.0)
    assert sig2[25] == 40.0
    assert sig2[0] == 0.0


def test_band_restricts_vertical_region():
    # две кривые в разных полосах: извлекаем только верхнюю
    h, w = 300, 100
    mask = np.zeros((h, w), dtype=bool)
    mask[48:52, :] = True    # верхняя линия y~50
    mask[248:252, :] = True  # нижняя линия y~250
    top = extract_trace_in_band(mask, y_top=0, y_bottom=150)
    assert np.nanmax(np.abs(top - 50)) < 2.0
