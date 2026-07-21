"""Общие операции над 1D-сигналом: пропуски, ресемплинг, сглаживание."""
from __future__ import annotations

import numpy as np


def fill_gaps(a: np.ndarray) -> np.ndarray:
    """Линейно заполняет NaN-пропуски."""
    a = a.copy()
    idx = np.arange(len(a))
    valid = ~np.isnan(a)
    if valid.sum() < 2:
        return np.nan_to_num(a)
    a[~valid] = np.interp(idx[~valid], idx[valid], a[valid])
    return a


def resample(a: np.ndarray, n_out: int) -> np.ndarray:
    """Линейный ресемплинг к n_out точкам."""
    if len(a) == 0:
        return np.zeros(n_out, dtype=np.float32)
    if len(a) == 1:
        return np.full(n_out, a[0], dtype=np.float32)
    src = np.linspace(0.0, 1.0, len(a))
    dst = np.linspace(0.0, 1.0, n_out)
    return np.interp(dst, src, a).astype(np.float32)


def smooth(a: np.ndarray, win: int = 3) -> np.ndarray:
    """Скользящее среднее (лёгкое сглаживание мелких зазубрин)."""
    if win <= 1 or len(a) < win:
        return a
    kernel = np.ones(win, dtype=np.float32) / win
    return np.convolve(a, kernel, mode="same").astype(np.float32)
