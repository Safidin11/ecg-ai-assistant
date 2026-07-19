"""Этап 1: предварительная обработка — удаление сетки и фона."""
from __future__ import annotations

from ecg_layout.preprocess import ink_mask, load_rgb
from pipeline.base import Stage
from pipeline.context import DigitizeContext


class PreprocessStage(Stage):
    name = "preprocess"

    def __init__(self, green_thresh: float = 0.5):
        self.green_thresh = green_thresh

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        ctx.rgb = load_rgb(ctx.image_path)
        ctx.ink_mask = ink_mask(ctx.rgb, self.green_thresh)
        ctx.note(f"preprocess: маска чернил {ctx.ink_mask.shape}, "
                 f"{ctx.ink_mask.mean() * 100:.1f}% пикселей")
        return ctx
