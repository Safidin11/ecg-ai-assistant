"""Этап 2 — Baseline detection: найти горизонтальные базовые линии отведений.

Базовая линия — строка с максимумом чернил внутри полосы отведения (изолиния).
Отведения расположены РЕГУЛЯРНО по вертикали, поэтому после первичного поиска
чиним пропуски:
  1. первичные линии — максимум чернил в каждой найденной полосе;
  2. оцениваем типичный шаг между линиями (медиана);
  3. где промежуток кратен шагу — вставляем пропущенные (плоские отведения);
  4. над первой / под последней — продлеваем, пока есть чернила.
Вставляем линию ТОЛЬКО если в этом месте реально есть трасса (полоса чернил на
всю ширину) — иначе не выдумываем строку в пустом промежутке (напр. до ритма).

Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.baselines import detect_row_bands
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s2_baseline_detection"


def _has_line_support(mask: np.ndarray, y: float, half: float, min_cover: float = 0.55) -> bool:
    """Есть ли у строки y горизонтальная линия-трасса на почти всю ширину?

    Считаем долю столбцов, где в полоске [y-half, y+half] есть чернила. У изолинии
    это почти вся ширина; у подписей/текста — лишь малая часть слева.
    """
    a = max(0, int(y - half))
    b = min(mask.shape[0], int(y + half) + 1)
    if b <= a:
        return False
    cols_with_ink = mask[a:b].any(axis=0)
    return float(cols_with_ink.mean()) >= min_cover


def _refine(baselines: list[int], mask: np.ndarray) -> list[int]:
    baselines = sorted(baselines)
    if len(baselines) < 2:
        return baselines
    h = mask.shape[0]
    s = float(np.median(np.diff(baselines)))       # типичный шаг между линиями
    if s <= 0:
        return baselines
    half = 0.3 * s
    result = set(baselines)

    # вставляем пропущенные линии внутри больших промежутков
    for i in range(len(baselines) - 1):
        gap = baselines[i + 1] - baselines[i]
        n = int(round(gap / s))
        for j in range(1, n):
            cand = baselines[i] + j * gap / n
            if _has_line_support(mask, cand, half):
                result.add(int(cand))

    # продлеваем вверх и вниз, пока есть линия-трасса
    cand = baselines[0] - s
    while cand > 0 and _has_line_support(mask, cand, half):
        result.add(int(cand))
        cand -= s
    cand = baselines[-1] + s
    while cand < h and _has_line_support(mask, cand, half):
        result.add(int(cand))
        cand += s
    return sorted(result)


def run(ctx: StageContext) -> StageContext:
    mask = ctx.ink_mask
    h, w = mask.shape
    proj = mask.sum(axis=1)                          # чернил в каждой строке
    bands = detect_row_bands(mask)

    initial = [int(y0 + int(np.argmax(proj[y0:y1]))) for y0, y1 in bands]
    baselines = _refine(initial, mask)

    ctx.bands = bands
    ctx.baselines = baselines
    added = len(baselines) - len(initial)
    ctx.note(f"{NAME}: линий {len(baselines)} (первично {len(initial)}, "
             f"дочинено +{added})")
    return ctx


def visualize(ctx: StageContext):
    """Показать базовые линии (зелёные) поверх очищенного изображения."""
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    w = img.width
    for i, y in enumerate(ctx.baselines or []):
        draw.line([(0, y), (w, y)], fill=(20, 160, 60), width=2)
        draw.text((4, max(0, y - 12)), f"#{i}", fill=(20, 120, 40))
    return img
