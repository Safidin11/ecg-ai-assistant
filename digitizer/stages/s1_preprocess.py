"""Этап 1 — Preprocess: из фото получить бинарное изображение (сигнал/текст).

По статье: убрать сетку и фон, оставить чернила. У нас сетка розовая/красная,
поэтому отделяем по зелёному каналу (сетка в нём светлая, чернила тёмные).
Правится независимо: меняешь только этот файл.
"""
from __future__ import annotations

from ecg_layout.preprocess import ink_mask, load_rgb, mask_to_image
from stages.context import StageContext

NAME = "s1_preprocess"


def run(ctx: StageContext, green_thresh: float = 0.5) -> StageContext:
    ctx.rgb = load_rgb(ctx.image_path)
    ctx.ink_mask = ink_mask(ctx.rgb, green_thresh)
    ctx.note(f"{NAME}: чернил {ctx.ink_mask.mean() * 100:.1f}% пикселей, "
             f"размер {ctx.ink_mask.shape}")
    return ctx


def visualize(ctx: StageContext):
    """Показать результат этапа: чёрные чернила на белом (сетка убрана)."""
    return mask_to_image(ctx.ink_mask).convert("RGB")
