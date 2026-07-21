"""Общая работа с изображением: загрузка и бинаризация (удаление сетки).

Метод бинаризации проверен на эталоне 12×1: яркость (HSV Value) делим на сильно
размытый фон (выравнивание освещения) и берём тёмное — так уходит сетка любого
цвета. Здесь это отдельная общая реализация (эталон не импортируем/не трогаем).
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def load_rgb(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def _trim_border(mask: np.ndarray, solid: float = 0.6) -> np.ndarray:
    """Обнуляет сплошную тёмную рамку по краям (проверенный порог 0.6)."""
    h, w = mask.shape
    ri, ci = mask.mean(axis=1), mask.mean(axis=0)
    t = 0
    while t < h and ri[t] > solid:
        t += 1
    b = h - 1
    while b > t and ri[b] > solid:
        b -= 1
    l = 0
    while l < w and ci[l] > solid:
        l += 1
    r = w - 1
    while r > l and ci[r] > solid:
        r -= 1
    out = np.zeros_like(mask)
    out[t:b + 1, l:r + 1] = mask[t:b + 1, l:r + 1]
    return out


def binarize(rgb: np.ndarray, thresh: float = 0.62, blur_frac: float = 1 / 30) -> np.ndarray:
    """Булева маска чернил (True = сигнал/текст). Сетку убирает по яркости,
    сплошную рамку — обрезкой краёв."""
    value = rgb.max(axis=2)
    h, w = value.shape
    radius = max(15, int(min(h, w) * blur_frac))
    val_img = Image.fromarray((value * 255).astype(np.uint8))
    bg = np.asarray(val_img.filter(ImageFilter.GaussianBlur(radius))) / 255.0
    flat = value / (bg + 1e-3)
    return _trim_border(flat < thresh)


def mask_to_image(mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.where(mask, 0, 255).astype(np.uint8))
