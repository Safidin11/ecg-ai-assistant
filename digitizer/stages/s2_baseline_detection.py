"""Этап 2 — Baseline detection: найти горизонтальные базовые линии отведений.

По статье базовые линии — это горизонтали с наибольшей плотностью сигнала.
Считаем «чернильный профиль» по строкам, находим полосы отведений и в каждой —
строку с максимумом чернил (изолиния, где трасса проводит больше всего времени).

Число найденных линий = число строк раскладки. Правится независимо.
"""
from __future__ import annotations

import numpy as np
from PIL import ImageDraw

from ecg_layout.baselines import detect_row_bands
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s2_baseline_detection"


def run(ctx: StageContext) -> StageContext:
    mask = ctx.ink_mask
    bands = detect_row_bands(mask)                 # (y0, y1) для каждой строки
    proj = mask.sum(axis=1)                         # чернил в каждой строке картинки

    baselines: list[int] = []
    for y0, y1 in bands:
        seg = proj[y0:y1]
        baselines.append(int(y0 + int(np.argmax(seg))))  # изолиния = максимум чернил

    ctx.bands = bands
    ctx.baselines = baselines
    ctx.note(f"{NAME}: найдено базовых линий: {len(baselines)}")
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
