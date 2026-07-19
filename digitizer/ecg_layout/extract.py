"""Извлечение сигнала из нарисованной кривой ЭКГ.

Для каждого столбца пикселей внутри полосы отведения берём «центр тяжести»
чёрных пикселей по вертикали — это и есть положение кривой в этом столбце.
Набор таких точек по всем столбцам = одномерный сигнал (пока в пикселях).

Дальше (отдельный шаг) сигнал калибруется в милливольты по сетке/масштабу.
Здесь — только геометрия: картинка кривой -> ряд чисел.
"""
from __future__ import annotations

import numpy as np


def extract_trace_in_band(
    ink_mask: np.ndarray,
    y_top: int,
    y_bottom: int,
    x_left: int = 0,
    x_right: int | None = None,
) -> np.ndarray:
    """Извлекает кривую в прямоугольной области (полосе отведения).

    Возвращает массив длины (x_right - x_left): для каждого столбца — Y-координата
    кривой в пикселях (в системе всей картинки). Где чернил нет — NaN.
    """
    h, w = ink_mask.shape
    y_top = max(0, int(y_top))
    y_bottom = min(h, int(y_bottom))
    x_left = max(0, int(x_left))
    x_right = w if x_right is None else min(w, int(x_right))

    sub = ink_mask[y_top:y_bottom, x_left:x_right].astype(np.float64)
    rows = np.arange(sub.shape[0])[:, None]  # индексы строк внутри полосы

    counts = sub.sum(axis=0)                 # сколько чернил в каждом столбце
    weighted = (sub * rows).sum(axis=0)      # сумма индексов строк с чернилами

    trace = np.full(sub.shape[1], np.nan)
    nonzero = counts > 0
    trace[nonzero] = weighted[nonzero] / counts[nonzero] + y_top
    return trace


def fill_gaps(trace: np.ndarray) -> np.ndarray:
    """Линейно заполняет пропуски (NaN) в кривой — там, где не было чернил."""
    trace = trace.copy()
    idx = np.arange(len(trace))
    valid = ~np.isnan(trace)
    if valid.sum() < 2:
        return trace
    trace[~valid] = np.interp(idx[~valid], idx[valid], trace[valid])
    return trace


def trace_to_signal(trace: np.ndarray, baseline: float | None = None) -> np.ndarray:
    """Переводит Y-пиксели в сигнал относительно базовой линии.

    В картинке Y растёт ВНИЗ, поэтому инвертируем: выше линии -> положительно.
    baseline — уровень изолинии в пикселях (по умолчанию медиана кривой).
    Значение всё ещё в «пикселях», калибровка в мВ — отдельный шаг.
    """
    filled = fill_gaps(trace)
    if baseline is None:
        baseline = float(np.nanmedian(filled))
    return baseline - filled
