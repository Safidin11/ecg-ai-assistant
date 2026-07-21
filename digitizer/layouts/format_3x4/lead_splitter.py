"""Нарезка изображения 3×4 на клетки отведений.

12 клеток = 3 строки × 4 колонки (+ ритм-полоса снизу). Каждая клетка начинается
ПОСЛЕ подписи отведения. Вертикальные границы — по правилу 0.7× расстояния между
базовыми линиями (как в эталоне).
"""
from __future__ import annotations

import numpy as np

from layouts.common.types import Cell
from layouts.format_3x4.config import CELL_MAP, N_COLS, N_ROWS, RHYTHM_LEAD, Config
from layouts.format_3x4.detector import Layout3x4


def _vertical_anchors(baselines: list[int], h: int, factor: float = 0.7) -> list[tuple[int, int]]:
    out = []
    for i, y in enumerate(baselines):
        d_up = (y - baselines[i - 1]) if i > 0 else (baselines[i + 1] - y if i + 1 < len(baselines) else h)
        d_dn = (baselines[i + 1] - y) if i + 1 < len(baselines) else (y - baselines[i - 1] if i > 0 else h)
        out.append((max(0, int(y - factor * d_up)), min(h, int(y + factor * d_dn))))
    return out


def _name_left(labels, top, bottom, left, right, name_w, pad):
    for lb in labels:
        if top <= lb["cy"] <= bottom and left - 5 <= lb["cx"] <= right:
            return int(lb["bbox"][0] + lb["bbox"][2]) + pad
    return int(left) + name_w + pad if name_w else int(left)


def split(mask: np.ndarray, layout: Layout3x4, labels: list[dict], cfg: Config) -> list[Cell]:
    h = mask.shape[0]
    baselines = layout.baselines
    cols = layout.col_bounds
    bounds = _vertical_anchors(baselines, h)
    name_w = int(np.median([lb["bbox"][2] for lb in labels])) if labels else 0

    cells: list[Cell] = []
    for r in range(min(N_ROWS, len(baselines))):
        top, bottom = bounds[r]
        baseline = baselines[r]
        for c, (left, right) in enumerate(cols):
            pad = int(0.02 * (right - left))
            cell_left = min(_name_left(labels, top, bottom, left, right, name_w, pad), int(right) - 1)
            cells.append(Cell(
                lead=CELL_MAP[(r, c)], row=r, col=c,
                box=(cell_left, int(top), int(right), int(bottom)),
                baseline=int(baseline),
                time_offset_s=c * cfg.col_seconds, duration_s=cfg.col_seconds,
            ))

    # ритм-полоса на всю ширину (если строк больше трёх)
    if len(baselines) > N_ROWS:
        r = N_ROWS
        top, bottom = bounds[r]
        x0, _, x1, _ = layout.content
        cells.append(Cell(
            lead=RHYTHM_LEAD, row=r, col=0,
            box=(int(x0), int(top), int(x1), int(bottom)),
            baseline=int(baselines[r]),
            time_offset_s=0.0, duration_s=cfg.duration_s, is_rhythm=True,
        ))
    return cells
