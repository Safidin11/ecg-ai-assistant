"""Этап 7 — Lead crop: выделить прямоугольник каждого отведения.

Клетка = пересечение строки (вертикальные якоря s4) и колонки (горизонтальные
якоря s6). Для каждой клетки запоминаем прямоугольник и её базовую линию.
Правится независимо.
"""
from __future__ import annotations

from PIL import ImageDraw

from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s7_lead_crop"


def run(ctx: StageContext) -> StageContext:
    rows = ctx.row_bounds or []
    cols = ctx.col_bounds or []
    baselines = ctx.baselines or []

    cells: list[dict] = []
    for r, (top, bottom) in enumerate(rows):
        baseline = baselines[r] if r < len(baselines) else (top + bottom) // 2
        for c, (left, right) in enumerate(cols):
            cells.append({
                "row": r, "col": c,
                "box": (int(left), int(top), int(right), int(bottom)),
                "baseline": int(baseline),
            })
    ctx.cells = cells
    ctx.note(f"{NAME}: клеток {len(cells)} ({len(rows)} строк x {len(cols)} колонок)")
    return ctx


def visualize(ctx: StageContext):
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    for cell in ctx.cells or []:
        l, t, r, b = cell["box"]
        draw.rectangle([l, t, r, b], outline=(30, 110, 230), width=2)
    return img
