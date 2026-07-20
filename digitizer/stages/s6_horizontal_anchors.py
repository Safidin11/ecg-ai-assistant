"""Этап 6 — Horizontal anchors: лево/право каждой колонки.

По статье подпись отведения стоит слева от своей колонки, поэтому x-позиции
подписей задают начала колонок. Кластеризуем x подписей → границы колонок:
левая = позиция подписи колонки, правая = начало следующей колонки (у последней —
правый край содержимого).

Не предполагаем равные колонки — берём реальные позиции. Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.infer import cluster_1d
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s6_horizontal_anchors"


def _content_x_range(mask: np.ndarray) -> tuple[int, int]:
    cols = np.where(mask.any(axis=0))[0]
    if len(cols) == 0:
        return 0, mask.shape[1]
    return int(cols[0]), int(cols[-1])


def run(ctx: StageContext) -> StageContext:
    mask = ctx.ink_mask
    x_min, x_max = _content_x_range(mask)
    labels = ctx.lead_labels or []

    if not labels:
        ctx.col_bounds = [(x_min, x_max)]           # без подписей — одна колонка
        ctx.note(f"{NAME}: подписей нет -> 1 колонка [{x_min},{x_max}]")
        return ctx

    # кластеризуем левые края подписей в колонки
    lefts = [lb["bbox"][0] for lb in labels]
    tol = 0.04 * mask.shape[1]
    ids = cluster_1d(lefts, tol=tol)
    n_cols = max(ids) + 1
    col_x = [int(np.mean([lefts[k] for k in range(len(lefts)) if ids[k] == c]))
             for c in range(n_cols)]
    col_x = sorted(col_x)

    bounds: list[tuple[int, int]] = []
    for i, x in enumerate(col_x):
        right = col_x[i + 1] if i + 1 < len(col_x) else x_max
        bounds.append((int(x), int(right)))
    ctx.col_bounds = bounds
    ctx.note(f"{NAME}: колонок {len(bounds)}: {bounds}")
    return ctx


def visualize(ctx: StageContext):
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    h = img.height
    for (left, right) in ctx.col_bounds or []:
        draw.line([(left, 0), (left, h)], fill=(230, 120, 20), width=3)
    draw.text((6, 4), f"колонок: {len(ctx.col_bounds or [])}", fill=(200, 30, 30))
    return img
