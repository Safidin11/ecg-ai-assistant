"""Извлечение сигнала из клеток 3×4 — через общий трекинг непрерывной кривой."""
from __future__ import annotations

import numpy as np

from layouts.common.tracking import track_curve
from layouts.common.types import Cell


def extract(mask: np.ndarray, cells: list[Cell]) -> dict:
    """(row, col) -> отклонение кривой от изолинии в пикселях."""
    out: dict = {}
    for cell in cells:
        out[(cell.row, cell.col)] = track_curve(mask, cell.box, cell.baseline)
    return out
