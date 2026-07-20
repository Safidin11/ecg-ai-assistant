"""Этап 8 — Signal extraction: из кривой в клетке получить 1D-сигнал.

Ключевая деталь — НАЛОЖЕНИЕ отведений: высокий зубец соседа залезает в полосу
текущего отведения. Поэтому берём не «центр всех чернил в столбце» (его тянет
к чужому зубцу), а СЛЕДИМ за непрерывной кривой: в каждом столбце выбираем
сегмент чернил, ближайший к предыдущей точке. Чужой зубец влетает далеко от
нашей линии и игнорируется. Отсчёт — от базовой линии; вверх = положительно.
Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.extract import fill_gaps
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s8_signal_extraction"


def _column_runs(rows: np.ndarray) -> list[tuple[int, int]]:
    """Разбивает индексы чернил в столбце на непрерывные сегменты (lo, hi)."""
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


def _track(mask: np.ndarray, box: tuple[int, int, int, int], baseline: int) -> np.ndarray:
    """Следит за кривой по столбцам, выбирая сегмент, ближайший к предыдущему.

    Возвращает отклонение от базовой линии в пикселях (вверх = положительно).
    """
    l, t, r, b = box
    sub = mask[t:b, l:r]
    n = sub.shape[1]
    base = baseline - t
    prev = float(base)
    dev = np.full(n, np.nan, dtype=np.float32)
    for x in range(n):
        idx = np.where(sub[:, x])[0]
        if len(idx) == 0:
            continue
        runs = _column_runs(idx)
        centers = np.array([(lo + hi) / 2.0 for lo, hi in runs])
        y = float(centers[int(np.argmin(np.abs(centers - prev)))])
        prev = y
        dev[x] = base - y                            # вверх = положительно
    return np.nan_to_num(fill_gaps(dev)).astype(np.float32)


def run(ctx: StageContext) -> StageContext:
    mask = ctx.ink_mask
    cell_signals: dict = {}
    for cell in ctx.cells or []:
        cell_signals[(cell["row"], cell["col"])] = _track(mask, cell["box"], cell["baseline"])
    ctx.cell_signals = cell_signals
    ctx.note(f"{NAME}: извлечено сигналов из {len(cell_signals)} клеток "
             f"(слежение за непрерывной кривой)")
    return ctx


def visualize(ctx: StageContext):
    """Красным поверх картинки — извлечённые кривые (проверка точности)."""
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    for cell in ctx.cells or []:
        l, t, r, b = cell["box"]
        dev = ctx.cell_signals.get((cell["row"], cell["col"]))
        if dev is None or len(dev) == 0:
            continue
        baseline = cell["baseline"]
        pts = [(l + x, int(baseline - dev[x])) for x in range(len(dev))]
        draw.line(pts, fill=(230, 30, 30), width=1)
    return img
