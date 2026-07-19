"""Этап 4: расположение отведений.

Формат выбрал пользователь -> раскладка известна детерминированно. Берём из
шаблона карту «(строка, колонка) -> отведение» и данные о ритм-полосе.
(Автоопределение формата по сигналу есть в ecg_layout.baselines и может
использоваться, когда пользователь выбрал «авто».)
"""
from __future__ import annotations

from ecg_layout.templates import LAYOUT_TEMPLATES, template_cell_map
from pipeline.base import Stage
from pipeline.context import DigitizeContext


class LayoutStage(Stage):
    name = "layout"

    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        spec = ctx.params.spec()
        template = spec["template"]
        cell_map = template_cell_map(template)          # (row,col) -> lead
        rhythm_leads = LAYOUT_TEMPLATES[template]["rhythm"]

        ctx.extra["layout"] = {
            "template": template,
            "rows": spec["rows"],
            "cols": spec["cols"],
            "rhythm": rhythm_leads,
            "cell_map": cell_map,
        }
        ctx.note(
            f"layout: {ctx.params.layout} -> {spec['rows']}x{spec['cols']}"
            f"{' + ритм ' + ','.join(rhythm_leads) if rhythm_leads else ''}"
        )
        return ctx
