"""Этап 5: калибровка сетки — перевод пикселей в мм, секунды и мВ.

Ключевая связь: полная ширина области сигнала соответствует длительности записи
(в каждой колонке своя доля времени, но суммарно по ширине — duration_s).
Отсюда:
    px_per_s  = ширина / duration_s
    px_per_mm = px_per_s / speed        (speed в мм/с)
    px_per_mV = px_per_mm * gain        (gain в мм/мВ)

Пиксели считаем квадратными (px/mm по горизонтали = по вертикали) — приближение
первого уровня. Позже отдельный детектор сетки может уточнить вертикальный масштаб.
"""
from __future__ import annotations

from pipeline.base import Stage
from pipeline.context import DigitizeContext


class GridStage(Stage):
    name = "grid"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        box = ctx.crop_box
        if box is None:
            h, w = ctx.ink_mask.shape
            box = (0, 0, w, h)
        x0, _, x1, _ = box
        width = max(1, x1 - x0)

        ctx.px_per_s = width / ctx.params.duration_s
        ctx.px_per_mm = ctx.px_per_s / ctx.params.speed
        ctx.px_per_mv = ctx.px_per_mm * ctx.params.gain

        ctx.note(
            f"grid: px_per_s={ctx.px_per_s:.1f}, px_per_mm={ctx.px_per_mm:.2f}, "
            f"px_per_mV={ctx.px_per_mv:.1f} (speed={ctx.params.speed}мм/с, gain={ctx.params.gain}мм/мВ)"
        )
        return ctx
