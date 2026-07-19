"""Препроцессинг картинки ЭКГ: удаление розовой/красной сетки.

Идея (из статьи Wu et al., Sci Rep 2022): сетка печатается розовым/красным, а
сигнал и подписи — чёрным. В зелёном канале розовая сетка светлая, а чёрные
чернила тёмные. Поэтому порог по зелёному каналу оставляет только чернила.

Работает для типичных красных/розовых сеток. Для серых сеток нужен другой
метод (напр. адаптивный порог) — это отмечено как ограничение.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def load_rgb(path: str) -> np.ndarray:
    """Загружает картинку как массив RGB float32 в диапазоне 0..1."""
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def ink_mask(rgb: np.ndarray, green_thresh: float = 0.5) -> np.ndarray:
    """Булева маска чернил: True — тёмное в зелёном канале (сигнал + подписи).

    Розовая сетка в зелёном канале светлая (> порога) и отсекается.
    """
    green = rgb[..., 1]
    return green < green_thresh


def remove_grid(path: str, green_thresh: float = 0.5) -> np.ndarray:
    """Возвращает булеву маску чернил для картинки по её пути."""
    return ink_mask(load_rgb(path), green_thresh)


def mask_to_image(mask: np.ndarray) -> Image.Image:
    """Булева маска -> чёрно-белая картинка (чернила чёрные на белом)."""
    arr = np.where(mask, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)
