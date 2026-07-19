"""Запуск последовательности этапов пайплайна."""
from __future__ import annotations

import time

from pipeline.base import Stage
from pipeline.context import DigitizeContext


class Pipeline:
    """Прогоняет контекст через список этапов по порядку.

    Список этапов можно менять/дополнять снаружи — пайплайн расширяемый.
    """

    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        for stage in self.stages:
            t0 = time.perf_counter()
            ctx = stage.run(ctx)
            dt = (time.perf_counter() - t0) * 1000
            ctx.note(f"{stage.name}: ok ({dt:.0f} ms)")
        return ctx

    def stage_names(self) -> list[str]:
        return [s.name for s in self.stages]
