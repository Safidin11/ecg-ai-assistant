"""Этап 8: нормализация — сборка канонического сигнала [12, N].

Каждое отведение ресемплируем на выбранную частоту (sampling_rate) и ставим на
его временную позицию в общей 10-секундной шкале. Отведения, у которых есть лишь
короткий сегмент (напр. 2.5 с в 3×4), занимают свой отрезок, остальное — нули.

Итог всегда одной формы [12, N] в каноническом порядке отведений — пригоден для
БД и модели (закрывает проблему разной длины у разных форматов).
"""
from __future__ import annotations

import numpy as np

from ecg_layout.leads import CANONICAL_LEADS, LEAD_TO_INDEX
from pipeline.base import Stage
from pipeline.context import DigitizeContext


def _resample(mv: np.ndarray, n_out: int) -> np.ndarray:
    """Ресемплирует сигнал к n_out точкам линейной интерполяцией."""
    if len(mv) == 0:
        return np.zeros(n_out, dtype=np.float32)
    if len(mv) == 1:
        return np.full(n_out, mv[0], dtype=np.float32)
    src = np.linspace(0.0, 1.0, len(mv))
    dst = np.linspace(0.0, 1.0, n_out)
    return np.interp(dst, src, mv).astype(np.float32)


class NormalizeStage(Stage):
    name = "normalize"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        sr = ctx.params.sampling_rate
        n_total = ctx.params.n_samples
        matrix = np.zeros((12, n_total), dtype=np.float32)

        for lead, info in ctx.extra["recon"].items():
            if lead not in LEAD_TO_INDEX:
                continue
            span_n = max(1, int(round(info["span_s"] * sr)))
            seg = _resample(info["mv"], span_n)
            start = int(round(info["offset_s"] * sr))
            end = min(n_total, start + span_n)
            row = LEAD_TO_INDEX[lead]
            matrix[row, start:end] = seg[: end - start]
            ctx.signals[lead] = matrix[row]

        ctx.signal_matrix = matrix
        covered = sorted(ctx.signals.keys())
        ctx.note(f"normalize: матрица {matrix.shape}, отведений с сигналом: "
                 f"{len(covered)}/12")
        return ctx
