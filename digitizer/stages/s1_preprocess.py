"""Этап 1 — Preprocess: из фото получить бинарное изображение (сигнал/текст).

Универсальная бинаризация (без привязки к цвету сетки):
  1. яркость = максимум по каналам (HSV Value): у чёрных чернил низкая, у любой
     сетки (розовой ИЛИ серой) и бумаги — высокая;
  2. выравнивание освещения: делим яркость на сильно размытую копию (оценка
     местного фона) → уходят тени и неравномерный свет, сетка усредняется в фон;
  3. порог: чернила = там, где яркость заметно ниже местного фона.

Кривая всегда темнее сетки, поэтому такой порог оставляет трассу и убирает сетку
любого цвета. Правится независимо: меняешь только этот файл.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from ecg_layout.preprocess import load_rgb, mask_to_image
from stages.context import StageContext

NAME = "s1_preprocess"


def _trim_border(mask: np.ndarray, solid: float = 0.6) -> np.ndarray:
    """Обнуляет сплошную тёмную рамку по краям (кадр фото/скан-поля).

    Край считается рамкой, пока строка/столбец почти сплошь чернила (> solid).
    Всё вне найденной области содержимого зануляется.
    """
    h, w = mask.shape
    row_ink = mask.mean(axis=1)
    col_ink = mask.mean(axis=0)
    t = 0
    while t < h and row_ink[t] > solid:
        t += 1
    b = h - 1
    while b > t and row_ink[b] > solid:
        b -= 1
    l = 0
    while l < w and col_ink[l] > solid:
        l += 1
    r = w - 1
    while r > l and col_ink[r] > solid:
        r -= 1
    out = np.zeros_like(mask)
    out[t:b + 1, l:r + 1] = mask[t:b + 1, l:r + 1]
    return out


def binarize(rgb: np.ndarray, thresh: float = 0.62, blur_frac: float = 1 / 30) -> np.ndarray:
    """Возвращает булеву маску чернил (True = сигнал/текст)."""
    value = rgb.max(axis=2)                      # HSV Value: тёмное = чернила
    h, w = value.shape
    radius = max(15, int(min(h, w) * blur_frac))  # крупное размытие = фон+сетка

    val_img = Image.fromarray((value * 255).astype(np.uint8))
    bg = np.asarray(val_img.filter(ImageFilter.GaussianBlur(radius))) / 255.0

    flat = value / (bg + 1e-3)                    # яркость относительно фона
    mask = flat < thresh                          # темнее фона = чернила
    return _trim_border(mask)                      # убрать тёмную рамку-кадр


def run(ctx: StageContext, thresh: float = 0.62) -> StageContext:
    ctx.rgb = load_rgb(ctx.image_path)
    ctx.ink_mask = binarize(ctx.rgb, thresh=thresh)
    ctx.note(f"{NAME}: чернил {ctx.ink_mask.mean() * 100:.1f}% пикселей, "
             f"размер {ctx.ink_mask.shape}")
    return ctx


def visualize(ctx: StageContext):
    """Показать результат этапа: чёрные чернила на белом (сетка убрана)."""
    return mask_to_image(ctx.ink_mask).convert("RGB")
