"""Этап 10 — Assemble: собрать цифровой сигнал [12, N].

Локализация (какое отведение в какой клетке) — из распознанного формата и
стандартного порядка отведений. Для каждой клетки берём её сигнал, переводим в
мВ, ресемплируем и ставим на нужную позицию по времени в общий массив [12, N].
Визуализация этапа — заново отрисованная чистая ЭКГ из этого сигнала.
"""
from __future__ import annotations

import numpy as np

from ecg_layout.leads import LEAD_TO_INDEX
from ecg_layout.templates import template_cell_map
from stages.context import StageContext

NAME = "s10_assemble"


def _format(n_cols: int) -> tuple[str, int, str]:
    """(шаблон, число строк сетки, имя формата для рендера)."""
    if n_cols <= 1:
        return "standard_12x1", 12, "12x1"
    if n_cols == 2:
        return "standard_6x2", 6, "6x2"
    return "standard_3x4", 3, "3x4"


def _resample(a: np.ndarray, n: int) -> np.ndarray:
    if len(a) == 0:
        return np.zeros(n, dtype=np.float32)
    if len(a) == 1:
        return np.full(n, a[0], dtype=np.float32)
    src = np.linspace(0, 1, len(a))
    dst = np.linspace(0, 1, n)
    return np.interp(dst, src, a).astype(np.float32)


def run(ctx: StageContext) -> StageContext:
    n_cols = len(ctx.col_bounds or [1])
    template, grid_rows, _ = _format(n_cols)
    cell_map = template_cell_map(template)

    sr, dur = ctx.sampling_rate, ctx.duration_s
    n_total = int(round(sr * dur))
    matrix = np.zeros((12, n_total), dtype=np.float32)
    seg_s = dur / n_cols
    seg_n = max(1, int(round(seg_s * sr)))
    px_per_mv = ctx.px_per_mv or 1.0

    for (row, col), dev in (ctx.cell_signals or {}).items():
        if row >= grid_rows:
            continue                                  # ритм-полоса — в [12,N] не нужна
        lead = cell_map.get((row, col))
        if lead is None or lead not in LEAD_TO_INDEX:
            continue
        mv = dev / px_per_mv
        seg = _resample(mv, seg_n)
        start = int(round(col * seg_s * sr))
        end = min(n_total, start + seg_n)
        matrix[LEAD_TO_INDEX[lead], start:end] = seg[: end - start]

    ctx.signal_matrix = matrix
    covered = int(np.count_nonzero(matrix.any(axis=1)))
    ctx.note(f"{NAME}: сигнал {matrix.shape}, отведений с данными {covered}/12 "
             f"(формат {_format(n_cols)[2]})")
    return ctx


def visualize(ctx: StageContext):
    """Заново отрисованная чистая ЭКГ из собранного сигнала."""
    import os
    import tempfile

    from PIL import Image

    from pipeline import ECGParams
    from pipeline.render import render_ecg

    _, _, fmt_name = _format(len(ctx.col_bounds or [1]))
    params = ECGParams(layout=fmt_name, speed=ctx.speed, gain=ctx.gain,
                       sampling_rate=ctx.sampling_rate, duration_s=ctx.duration_s)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    render_ecg(ctx.signal_matrix, params, tmp)
    img = Image.open(tmp).convert("RGB")
    img.load()
    os.remove(tmp)
    return img
