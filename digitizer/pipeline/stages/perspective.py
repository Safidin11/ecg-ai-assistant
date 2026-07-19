"""Этап 2: коррекция перспективы (наклон/разворот бумаги).

ЗАГЛУШКА: пока пропускает изображение как есть. Отдельный модуль, чтобы позже
подключить реальную коррекцию (поиск четырёх углов листа + гомография) без
изменения остального пайплайна.
"""
from __future__ import annotations

from pipeline.base import Stage
from pipeline.context import DigitizeContext


class PerspectiveStage(Stage):
    name = "perspective"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        # TODO: определить углы листа и выпрямить (cv2.getPerspectiveTransform).
        ctx.note("perspective: пропущено (заглушка)")
        return ctx
