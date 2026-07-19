"""Этап 7: восстановление сигнала — из пиксельной кривой в милливольты.

Для каждого отведения:
  1. заполняем пропуски в кривой;
  2. изолиния = медиана кривой; отклонение вверх (меньший Y) -> положительный сигнал;
  3. пиксели -> мВ через калибровку (px_per_mV).
Результат — сигнал в мВ на исходном пиксельном разрешении (ресемплинг — далее).
"""
from __future__ import annotations

import numpy as np

from ecg_layout.extract import fill_gaps
from pipeline.base import Stage
from pipeline.context import DigitizeContext


class ReconstructStage(Stage):
    name = "reconstruct"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        px_per_mv = ctx.px_per_mv or 1.0
        recon: dict[str, dict] = {}

        for lead, info in ctx.extra["lead_traces"].items():
            trace = fill_gaps(info["trace"])
            if np.all(np.isnan(trace)):
                mv = np.zeros(len(trace), dtype=np.float32)
            else:
                baseline = float(np.nanmedian(trace))
                deviation_px = baseline - trace          # вверх = положительно
                mv = (deviation_px / px_per_mv).astype(np.float32)
                mv = np.nan_to_num(mv)
            recon[lead] = {
                "mv": mv,
                "offset_s": info["offset_s"],
                "span_s": info["span_s"],
            }
            ctx.traces[lead] = info["trace"]  # сохраняем пиксельную кривую для отладки

        ctx.extra["recon"] = recon
        ctx.note(f"reconstruct: сигналы в мВ для {len(recon)} отведений")
        return ctx
