"""Этап 6: извлечение кривых ЭКГ.

Раскладка известна -> делим область сигнала на ФИКСИРОВАННОЕ число равных полос
(строк) и колонок по выбранному формату. Для каждой клетки берём кривую
(y-центроид по столбцам). Так соседние отведения не «слипаются» — извлекаются
все 12 (в т.ч. те, чьи подписи OCR не читает).
"""
from __future__ import annotations

from ecg_layout.extract import extract_trace_in_band
from pipeline.base import Stage
from pipeline.context import DigitizeContext


class ExtractStage(Stage):
    name = "extract"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        mask = ctx.ink_mask
        layout = ctx.extra["layout"]
        rows, cols = layout["rows"], layout["cols"]
        cell_map = layout["cell_map"]
        rhythm_leads = layout["rhythm"]

        x0, y0, x1, y1 = ctx.crop_box or (0, 0, mask.shape[1], mask.shape[0])
        n_bands = rows + len(rhythm_leads)
        band_h = (y1 - y0) / n_bands
        col_w = (x1 - x0) / cols
        span_col = ctx.params.duration_s / cols

        lead_traces: dict[str, dict] = {}

        # основная сетка: rows x cols
        for r in range(rows):
            by0 = y0 + r * band_h
            by1 = y0 + (r + 1) * band_h
            for c in range(cols):
                sx0 = x0 + c * col_w
                sx1 = x0 + (c + 1) * col_w
                lead = cell_map.get((r, c))
                if lead is None:
                    continue
                trace = extract_trace_in_band(mask, by0, by1, sx0, sx1)
                lead_traces[lead] = {
                    "trace": trace,
                    "offset_s": c * span_col,
                    "span_s": span_col,
                    "is_rhythm": False,
                }

        # ритм-полосы (на всю ширину, снизу) — дают полные 10 с для своего отведения
        for i, lead in enumerate(rhythm_leads):
            by0 = y0 + (rows + i) * band_h
            by1 = y0 + (rows + i + 1) * band_h
            trace = extract_trace_in_band(mask, by0, by1, x0, x1)
            lead_traces[lead] = {          # заменяем короткий сегмент полным
                "trace": trace,
                "offset_s": 0.0,
                "span_s": ctx.params.duration_s,
                "is_rhythm": True,
            }

        ctx.extra["lead_traces"] = lead_traces
        ctx.note(f"extract: извлечено кривых: {len(lead_traces)} "
                 f"({rows}x{cols}{' +ритм' if rhythm_leads else ''})")
        return ctx
