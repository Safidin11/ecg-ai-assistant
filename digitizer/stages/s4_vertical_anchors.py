"""Этап 4 — Vertical anchors: верхняя и нижняя граница каждого отведения.

По статье: границы = 0.7 × расстояния до соседней базовой линии (сверху и снизу).
Это даёт вертикальную область каждого отведения для последующей обрезки,
устойчиво к неравномерным промежуткам. Правится независимо.
"""
from __future__ import annotations

from PIL import ImageDraw

from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s4_vertical_anchors"
_FACTOR = 0.7


def run(ctx: StageContext) -> StageContext:
    bl = ctx.baselines or []
    h = ctx.ink_mask.shape[0]
    bounds: list[tuple[int, int]] = []
    for i, y in enumerate(bl):
        d_up = (y - bl[i - 1]) if i > 0 else (bl[i + 1] - y if i + 1 < len(bl) else h)
        d_dn = (bl[i + 1] - y) if i + 1 < len(bl) else (y - bl[i - 1] if i > 0 else h)
        top = max(0, int(y - _FACTOR * d_up))
        bottom = min(h, int(y + _FACTOR * d_dn))
        bounds.append((top, bottom))
    ctx.row_bounds = bounds
    ctx.note(f"{NAME}: вертикальные якоря для {len(bounds)} отведений")
    return ctx


def visualize(ctx: StageContext):
    """Показать области отведений (верх/низ) поверх изображения."""
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    w = img.width
    for i, (top, bottom) in enumerate(ctx.row_bounds or []):
        draw.rectangle([1, top, w - 2, bottom], outline=(230, 120, 20), width=2)
        y = ctx.baselines[i]
        draw.line([(0, y), (w, y)], fill=(20, 160, 60), width=1)  # изолиния
    return img
