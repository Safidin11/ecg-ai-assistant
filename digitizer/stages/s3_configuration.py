"""Этап 3 — Configuration: определить конфигурацию раскладки.

По статье число строк ЭКГ определяется числом базовых линий. Само число колонок
(формат 3×4 / 6×2 / 12×1) уточняется позже, на горизонтальных якорях по подписям.
Здесь фиксируем n_rows и даём первичную догадку формата по числу строк.
Правится независимо.
"""
from __future__ import annotations

from PIL import ImageDraw

from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s3_configuration"


def _guess_format(n_rows: int) -> str:
    if n_rows <= 4:
        return "≈ 3×4 (3 строки + возможная ритм-полоса)"
    if n_rows <= 8:
        return "≈ 6×2"
    return "≈ 12×1"


def run(ctx: StageContext) -> StageContext:
    ctx.n_rows = len(ctx.baselines or [])
    ctx.note(f"{NAME}: строк = {ctx.n_rows} -> {_guess_format(ctx.n_rows)}")
    return ctx


def visualize(ctx: StageContext):
    """Показать полосы строк рамками и подпись о конфигурации."""
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    w = img.width
    for y0, y1 in ctx.bands or []:
        draw.rectangle([1, y0, w - 2, y1], outline=(30, 110, 230), width=2)
    draw.text((6, 4), f"строк: {ctx.n_rows}  |  {_guess_format(ctx.n_rows or 0)}",
              fill=(200, 30, 30))
    return img
