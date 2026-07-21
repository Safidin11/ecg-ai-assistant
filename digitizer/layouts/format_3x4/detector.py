"""Детектор раскладки 3×4 — специализированный (не универсальный).

Формат фиксирован: 3 строки сетки + ритм-полоса, 4 колонки. Поэтому детектор
уверенный: обрезает лист, находит ровно 3 строки (+ ритм) и 4 колонки, а не
пытается угадывать «вообще всё».
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ecg_layout.baselines import detect_row_bands  # проверенная детекция полос
from layouts.format_3x4.config import N_COLS, N_ROWS


@dataclass
class Layout3x4:
    content: tuple[int, int, int, int]       # (x0, y0, x1, y1) области сигнала
    row_bands: list[tuple[int, int]]         # (top, bottom) для строк (3 сетки + ритм)
    baselines: list[int]                     # y изолинии каждой строки
    col_bounds: list[tuple[int, int]]        # (left, right) для 4 колонок


def _content_box(mask: np.ndarray, empty: float = 0.003) -> tuple[int, int, int, int]:
    """Область содержимого: срезаем пустые поля и ПЛОТНУЮ рамку по краям.

    Рамка (даже не сплошная) заметно плотнее обычной сигнальной строки/столбца,
    поэтому порог берём относительно типичной плотности сигнала.
    """
    h, w = mask.shape
    ri, ci = mask.mean(axis=1), mask.mean(axis=0)
    sig_r = np.median(ri[ri > empty]) if np.any(ri > empty) else 0.05
    sig_c = np.median(ci[ci > empty]) if np.any(ci > empty) else 0.05
    dense_r = max(0.12, 5 * sig_r)
    dense_c = max(0.12, 5 * sig_c)

    def _edge(profile, n, dense):
        lo = 0
        while lo < n and (profile[lo] > dense or profile[lo] < empty):
            lo += 1
        hi = n - 1
        while hi > lo and (profile[hi] > dense or profile[hi] < empty):
            hi -= 1
        return lo, hi

    y0, y1 = _edge(ri, h, dense_r)
    x0, x1 = _edge(ci, w, dense_c)
    if x1 <= x0 or y1 <= y0:
        return 0, 0, w, h
    return x0, y0, x1, y1


def _row_bands(mask: np.ndarray, y0: int, y1: int, active_frac: float = 0.05) -> list[tuple[int, int]]:
    """Полосы строк по горизонтальному профилю чернил в области [y0, y1]."""
    proj = mask[y0:y1].sum(axis=1).astype(float)
    if proj.max() <= 0:
        return []
    active = proj > proj.max() * active_frac
    bands, start = [], None
    for i, a in enumerate(active):
        if a and start is None:
            start = i
        elif not a and start is not None:
            bands.append((y0 + start, y0 + i))
            start = None
    if start is not None:
        bands.append((y0 + start, y1))
    return bands


def _merge_close(bands: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Сливает соседние полосы с малым разрывом (подавляет переразбиение строки)."""
    if len(bands) <= 1:
        return bands
    heights = [b - a for a, b in bands]
    med = np.median(heights)
    merged = [list(bands[0])]
    for a, b in bands[1:]:
        if a - merged[-1][1] < 0.15 * med:            # сливаем только крошечные разрывы
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def _columns_from_labels(labels, x0: int, x1: int) -> list[tuple[int, int]]:
    """4 колонки из x-позиций подписей; иначе — ровное деление ширины на 4."""
    lefts = sorted(lb["bbox"][0] for lb in labels)
    if lefts:
        tol = 0.04 * (x1 - x0)
        centers = []
        for x in lefts:
            if not centers or x - centers[-1][-1] > tol:
                centers.append([x])
            else:
                centers[-1].append(x)
        cols = [int(np.mean(c)) for c in centers]
        if len(cols) == N_COLS:                       # ровно 4 — доверяем
            bounds = []
            for i, c in enumerate(cols):
                right = cols[i + 1] if i + 1 < len(cols) else x1
                bounds.append((int(c), int(right)))
            return bounds
    # запасной вариант: ровно 4 равные колонки (формат это допускает)
    step = (x1 - x0) / N_COLS
    return [(int(x0 + i * step), int(x0 + (i + 1) * step)) for i in range(N_COLS)]


def detect(mask: np.ndarray, labels: list[dict]) -> Layout3x4:
    x0, y0, x1, y1 = _content_box(mask)

    # Строки ищем ТОЛЬКО в области содержимого (без верхних/боковых полей и мусора),
    # иначе подписи/остаток рамки склеивают строки.
    content = mask[y0:y1, x0:x1]
    bands = _merge_close(detect_row_bands(content))
    bands = [(a + y0, b + y0) for a, b in bands]       # обратно в координаты картинки

    proj = mask[:, x0:x1].sum(axis=1)                  # плотность по строкам внутри содержимого
    baselines = [int(a + int(np.argmax(proj[a:b]))) for a, b in bands]

    col_bounds = _columns_from_labels(labels, x0, x1)
    return Layout3x4(content=(x0, y0, x1, y1), row_bands=bands,
                     baselines=baselines, col_bounds=col_bounds)
