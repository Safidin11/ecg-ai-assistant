"""Этап 7 — Lead crop: выделить прямоугольник каждого отведения.

Клетка = пересечение строки (вертикальные якоря s4) и колонки (горизонтальные
якоря s6). Для каждой клетки запоминаем прямоугольник и её базовую линию.
Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s7_lead_crop"


def _name_in_cell(labels, top, bottom, left, right):
    """Подпись отведения, попадающая в эту клетку (по позиции), или None."""
    for lb in labels:
        if top <= lb["cy"] <= bottom and left - 5 <= lb["cx"] <= right:
            return lb
    return None


def run(ctx: StageContext) -> StageContext:
    rows = ctx.row_bounds or []
    cols = ctx.col_bounds or []
    baselines = ctx.baselines or []
    labels = ctx.lead_labels or []
    # запасная ширина подписи (если для клетки подпись не распозналась)
    name_w = int(np.median([lb["bbox"][2] for lb in labels])) if labels else 0

    cells: list[dict] = []
    for r, (top, bottom) in enumerate(rows):
        baseline = baselines[r] if r < len(baselines) else (top + bottom) // 2
        for c, (left, right) in enumerate(cols):
            pad = int(0.02 * (right - left))
            name = _name_in_cell(labels, top, bottom, left, right)
            if name is not None:                     # начинаем ПОСЛЕ подписи
                nx, _, nw, _ = name["bbox"]
                cell_left = int(nx + nw) + pad
            elif name_w:
                cell_left = int(left) + name_w + pad
            else:
                cell_left = int(left)
            cell_left = min(cell_left, int(right) - 1)
            cells.append({
                "row": r, "col": c,
                "box": (cell_left, int(top), int(right), int(bottom)),
                "baseline": int(baseline),
            })
    ctx.cells = cells
    ctx.note(f"{NAME}: клеток {len(cells)} ({len(rows)} строк x {len(cols)} колонок, "
             f"обрезка после подписей)")
    return ctx


def visualize(ctx: StageContext):
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    for cell in ctx.cells or []:
        l, t, r, b = cell["box"]
        draw.rectangle([l, t, r, b], outline=(30, 110, 230), width=2)
    return img
