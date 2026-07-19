"""Общий контекст, который проходит через все этапы пайплайна.

Каждый этап читает нужные поля и дописывает свои результаты. Так этапы не
зависят друг от друга напрямую и легко переставляются/заменяются.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from pipeline.params import ECGParams


@dataclass
class DigitizeContext:
    image_path: str
    params: ECGParams

    # заполняется этапами по ходу пайплайна:
    rgb: np.ndarray | None = None              # исходное изображение RGB (0..1)
    ink_mask: np.ndarray | None = None         # маска чернил (сетка убрана)
    crop_box: tuple[int, int, int, int] | None = None  # (x0, y0, x1, y1) области сигнала

    px_per_mm: float | None = None             # калибровка: пикселей на мм
    px_per_s: float | None = None              # пикселей на секунду (по скорости)
    px_per_mv: float | None = None             # пикселей на мВ (по усилению)

    # traces: имя отведения -> сигнал в пикселях (относительно изолинии)
    traces: dict[str, np.ndarray] = field(default_factory=dict)
    # signals: имя отведения -> сигнал в мВ на sampling_rate, длиной n_samples
    signals: dict[str, np.ndarray] = field(default_factory=dict)
    # итоговая матрица [12, N] в мВ (канонический порядок отведений)
    signal_matrix: np.ndarray | None = None

    # диагностика/отладка каждого этапа
    log: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def note(self, message: str) -> None:
        self.log.append(message)
