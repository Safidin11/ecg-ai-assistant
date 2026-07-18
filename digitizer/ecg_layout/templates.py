"""Готовые шаблоны раскладок — запасной вариант, когда OCR не справился.

Если подписей на картинке нет или OCR не уверен, мы не угадываем по позициям,
а берём известную стандартную раскладку и делим картинку на равномерную сетку.
Так же поступают Open-ECG-Digitizer и победитель PhysioNet 2024.
"""
from __future__ import annotations

from ecg_layout.types import LayoutMap, LeadCell

# Каждый шаблон: grid — отведения по строкам/колонкам основной сетки;
# rhythm — список полноширинных ритм-полос (стопкой снизу), может быть пустым.
LAYOUT_TEMPLATES: dict[str, dict] = {
    "standard_3x4": {
        "grid": [
            ["I", "aVR", "V1", "V4"],
            ["II", "aVL", "V2", "V5"],
            ["III", "aVF", "V3", "V6"],
        ],
        "rhythm": ["II"],
    },
    "standard_3x4_no_rhythm": {
        "grid": [
            ["I", "aVR", "V1", "V4"],
            ["II", "aVL", "V2", "V5"],
            ["III", "aVF", "V3", "V6"],
        ],
        "rhythm": [],
    },
    "standard_6x2": {
        "grid": [
            ["I", "V1"],
            ["II", "V2"],
            ["III", "V3"],
            ["aVR", "V4"],
            ["aVL", "V5"],
            ["aVF", "V6"],
        ],
        "rhythm": [],
    },
    "standard_12x1": {
        "grid": [[lead] for lead in
                 ["I", "II", "III", "aVR", "aVL", "aVF",
                  "V1", "V2", "V3", "V4", "V5", "V6"]],
        "rhythm": [],
    },
}


def available_templates() -> list[str]:
    return list(LAYOUT_TEMPLATES.keys())


def template_grid_dims(name: str) -> tuple[int, int]:
    """(число строк сетки, число колонок) для шаблона (без ритм-полос)."""
    grid = LAYOUT_TEMPLATES[name]["grid"]
    return len(grid), max(len(r) for r in grid)


def template_cell_map(name: str) -> dict[tuple[int, int], str]:
    """Отображение (строка, колонка) -> отведение для сетки шаблона."""
    grid = LAYOUT_TEMPLATES[name]["grid"]
    return {(r, c): lead for r, leads in enumerate(grid) for c, lead in enumerate(leads)}


def build_layout_from_template(
    name: str,
    image_w: float,
    image_h: float,
    total_seconds: float = 10.0,
) -> LayoutMap:
    """Строит карту раскладки из шаблона, разбивая картинку на равные клетки.

    Клетки получают bbox = прямоугольник клетки на картинке (а не рамку
    подписи, как в OCR-режиме), и те же временные отрезки по колонкам.
    """
    if name not in LAYOUT_TEMPLATES:
        raise ValueError(f"Неизвестный шаблон: {name}. Доступны: {available_templates()}")

    tmpl = LAYOUT_TEMPLATES[name]
    grid: list[list[str]] = tmpl["grid"]
    rhythm: list[str] = tmpl["rhythm"]

    n_grid_rows = len(grid)
    n_cols = max(len(r) for r in grid)
    n_bands = n_grid_rows + len(rhythm)  # ритм-полосы идут отдельными строками снизу
    band_h = image_h / n_bands
    seg = total_seconds / n_cols

    cells: list[LeadCell] = []

    # основная сетка
    for r, leads in enumerate(grid):
        cols_in_row = len(leads)
        col_w = image_w / cols_in_row
        y = r * band_h
        for c, lead in enumerate(leads):
            x = c * col_w
            cells.append(
                LeadCell(
                    lead=lead,
                    row=r,
                    col=c,
                    bbox=(x, y, col_w, band_h),
                    time_offset_s=c * seg,
                    duration_s=seg,
                    is_rhythm=False,
                    conf=0.0,  # шаблон: значение не измерено, а предположено
                )
            )

    # ритм-полосы (на всю ширину, стопкой ниже сетки)
    for i, lead in enumerate(rhythm):
        r = n_grid_rows + i
        y = r * band_h
        cells.append(
            LeadCell(
                lead=lead,
                row=r,
                col=0,
                bbox=(0.0, y, image_w, band_h),
                time_offset_s=0.0,
                duration_s=total_seconds,
                is_rhythm=True,
                conf=0.0,
            )
        )

    return LayoutMap(
        n_rows=n_bands,
        n_cols=n_cols,
        total_seconds=total_seconds,
        cells=cells,
        source=f"template:{name}",
    )
