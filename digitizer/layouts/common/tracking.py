"""Слежение за непрерывной кривой — общий извлекатель сигнала.

Проверенная на 12×1 победа над НАЛОЖЕНИЕМ отведений: не «центр всех чернил»
(его тянет к чужому зубцу), а следим за кривой — в каждом столбце берём сегмент
чернил, ближайший к предыдущей точке. Слишком далёкий прыжок (артефакт: чёрточка,
калибровочный импульс, рамка) пропускаем. В конце центрируем по изолинии и режем
грубые выбросы.
"""
from __future__ import annotations

import numpy as np

from layouts.common.signal import fill_gaps


def _column_runs(rows: np.ndarray) -> list[tuple[int, int]]:
    """Непрерывные сегменты чернил в столбце: [(lo, hi), ...]."""
    runs = []
    start = prev = rows[0]
    for v in rows[1:]:
        if v == prev + 1:
            prev = v
        else:
            runs.append((start, prev))
            start = prev = v
    runs.append((start, prev))
    return runs


def track_curve(mask: np.ndarray, box: tuple[int, int, int, int], baseline: int,
                max_jump_frac: float = 0.22, cap_frac: float = 1.5) -> np.ndarray:
    """Извлекает отклонение кривой от базовой линии (в пикселях, вверх = +).

    box — (left, top, right, bottom); baseline — y изолинии в системе картинки.
    """
    left, top, right, bottom = box
    sub = mask[top:bottom, left:right]
    height, n = sub.shape
    if n <= 0 or height <= 0:
        return np.zeros(max(0, right - left), dtype=np.float32)
    base = baseline - top
    max_jump = max_jump_frac * height
    prev = float(base)
    dev = np.full(n, np.nan, dtype=np.float32)
    for x in range(n):
        idx = np.where(sub[:, x])[0]
        if len(idx) == 0:
            continue
        centers = np.array([(lo + hi) / 2.0 for lo, hi in _column_runs(idx)])
        y = float(centers[int(np.argmin(np.abs(centers - prev)))])
        if abs(y - prev) > max_jump:                 # артефакт — пропускаем
            continue
        prev = y
        dev[x] = base - y

    dev = fill_gaps(dev)
    dev = dev - np.nanmedian(dev)                     # центрируем по изолинии
    cap = cap_frac * height
    return np.clip(dev, -cap, cap).astype(np.float32)
