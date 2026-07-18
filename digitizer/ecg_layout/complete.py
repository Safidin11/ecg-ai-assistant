"""Достройка раскладки по стандартному шаблону.

Идея: если OCR прочитал часть отведений, и их позиции ТОЧНО совпадают с одной
из стандартных раскладок, то пропущенные клетки можно достроить по этому
шаблону (например, левый столбец I/II/III, который OCR почти никогда не берёт —
это одиночные вертикальные палочки).

Важно: достроенные отведения помечаются inferred=True и conf=0.0 — они НЕ
прочитаны, а выведены из раскладки. Это должно быть видно дальше по пайплайну.
"""
from __future__ import annotations

from ecg_layout.templates import (
    LAYOUT_TEMPLATES,
    template_cell_map,
    template_grid_dims,
)
from ecg_layout.types import LayoutMap, LeadCell

# Минимум прочитанных клеток, чтобы доверять совпадению с шаблоном.
_MIN_MATCH = 4


def complete_layout(layout: LayoutMap, image_w: float, image_h: float) -> LayoutMap:
    """Достраивает пропущенные отведения, если раскладка совпала со стандартом.

    Возвращает тот же layout (дополненный на месте). Если ни один шаблон не
    подошёл без противоречий — ничего не меняет.
    """
    grid_cells = [c for c in layout.cells if not c.is_rhythm]
    if not grid_cells:
        return layout

    n_grid_rows = max(c.row for c in grid_cells) + 1
    read: dict[tuple[int, int], str] = {(c.row, c.col): c.lead for c in grid_cells}

    # Ищем шаблон тех же размеров, с которым прочитанные клетки НЕ противоречат.
    best_name = None
    best_match = -1
    for name in LAYOUT_TEMPLATES:
        rows, cols = template_grid_dims(name)
        if rows != n_grid_rows or cols != layout.n_cols:
            continue
        cmap = template_cell_map(name)
        mismatches = sum(1 for pos, lead in read.items() if cmap.get(pos) != lead)
        matches = sum(1 for pos, lead in read.items() if cmap.get(pos) == lead)
        if mismatches == 0 and matches >= _MIN_MATCH and matches > best_match:
            best_name, best_match = name, matches

    if best_name is None:
        return layout

    cmap = template_cell_map(best_name)
    seg = layout.total_seconds / layout.n_cols
    n_rhythm_rows = len({c.row for c in layout.cells if c.is_rhythm})
    band_h = image_h / (n_grid_rows + n_rhythm_rows) if (n_grid_rows + n_rhythm_rows) else image_h
    cell_w = image_w / layout.n_cols

    added = 0
    for (r, c), lead in cmap.items():
        if (r, c) in read:
            continue
        layout.cells.append(
            LeadCell(
                lead=lead,
                row=r,
                col=c,
                bbox=(c * cell_w, r * band_h, cell_w, band_h),
                time_offset_s=c * seg,
                duration_s=seg,
                is_rhythm=False,
                conf=0.0,
                inferred=True,  # достроено, не прочитано
            )
        )
        added += 1

    if added:
        layout.source = f"{layout.source}+completed:{best_name}"
    return layout
