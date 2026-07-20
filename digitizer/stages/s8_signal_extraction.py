"""Этап 8 — Signal extraction: из кривой в клетке получить 1D-сигнал.

Для каждого столбца клетки берём центр чернил по вертикали (положение кривой),
отсчёт — от базовой линии этой клетки; вверх (меньший Y) = положительное
отклонение. Пока в пикселях; перевод в мВ — на этапе s9. Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.extract import extract_trace_in_band, fill_gaps
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s8_signal_extraction"


def run(ctx: StageContext) -> StageContext:
    mask = ctx.ink_mask
    cell_signals: dict = {}
    for cell in ctx.cells or []:
        l, t, r, b = cell["box"]
        trace = fill_gaps(extract_trace_in_band(mask, t, b, l, r))
        baseline = cell["baseline"]
        deviation = baseline - trace                 # вверх = положительно
        deviation = np.nan_to_num(deviation).astype(np.float32)
        cell_signals[(cell["row"], cell["col"])] = deviation
    ctx.cell_signals = cell_signals
    ctx.note(f"{NAME}: извлечено сигналов из {len(cell_signals)} клеток")
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
