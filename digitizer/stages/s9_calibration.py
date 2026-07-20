"""Этап 9 — Calibration: перевод пикселей во время и милливольты.

Полная ширина содержимого соответствует длительности записи (в каждой колонке
своя доля времени, но суммарно по ширине — duration_s). Отсюда:
    px_per_s  = ширина_содержимого / duration_s
    px_per_mm = px_per_s / speed
    px_per_mV = px_per_mm * gain
Пиксели считаем квадратными (по горизонтали = по вертикали). Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s9_calibration"


def run(ctx: StageContext) -> StageContext:
    cols = ctx.col_bounds or []
    if cols:
        content_w = cols[-1][1] - cols[0][0]
    else:
        content_w = ctx.ink_mask.shape[1]
    content_w = max(1, content_w)

    ctx.px_per_s = content_w / ctx.duration_s
    px_per_mm = ctx.px_per_s / ctx.speed
    ctx.px_per_mv = px_per_mm * ctx.gain
    ctx.note(f"{NAME}: px_per_s={ctx.px_per_s:.1f}, px_per_mV={ctx.px_per_mv:.1f} "
             f"(speed={ctx.speed}мм/с, gain={ctx.gain}мм/мВ)")
    return ctx


def visualize(ctx: StageContext):
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((6, 4),
              f"px/s={ctx.px_per_s:.0f}  px/mV={ctx.px_per_mv:.0f}  "
              f"({ctx.speed}мм/с, {ctx.gain}мм/мВ)", fill=(200, 30, 30))
    return img
