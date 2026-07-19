"""Этап 3: обрезка — оставляем прямоугольник, где реально есть сигнал.

Берём ограничивающий прямоугольник чернил (с небольшим отступом). Это убирает
пустые поля и рамки. crop_box кладём в контекст; сам массив не режем, чтобы
координаты подписей/сетки оставались в исходной системе.
"""
from __future__ import annotations

import numpy as np

from pipeline.base import Stage
from pipeline.context import DigitizeContext


class CropStage(Stage):
    name = "crop"

    def __init__(self, pad_frac: float = 0.01):
        self.pad_frac = pad_frac

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        mask = ctx.ink_mask
        if mask is None:
            ctx.note("crop: нет маски — пропуск")
            return ctx
        h, w = mask.shape
        cols = np.where(mask.any(axis=0))[0]
        rows = np.where(mask.any(axis=1))[0]
        if len(cols) == 0 or len(rows) == 0:
            ctx.crop_box = (0, 0, w, h)
            ctx.note("crop: чернил нет — вся картинка")
            return ctx
        pad_x = int(self.pad_frac * w)
        pad_y = int(self.pad_frac * h)
        x0 = max(0, int(cols[0]) - pad_x)
        x1 = min(w, int(cols[-1]) + 1 + pad_x)
        y0 = max(0, int(rows[0]) - pad_y)
        y1 = min(h, int(rows[-1]) + 1 + pad_y)
        ctx.crop_box = (x0, y0, x1, y1)
        ctx.note(f"crop: область сигнала x=[{x0},{x1}] y=[{y0},{y1}]")
        return ctx
