"""Общие типы данных для всех форматных пайплайнов."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Cell:
    """Одна клетка отведения: положение, базовая линия, время."""

    lead: str
    row: int
    col: int
    box: tuple[int, int, int, int]      # (left, top, right, bottom)
    baseline: int                       # y изолинии
    time_offset_s: float = 0.0          # смещение по времени в общей записи
    duration_s: float = 0.0             # длительность куска (сек)
    is_rhythm: bool = False


@dataclass
class DigitizeResult:
    """Итог оцифровки — единый для всех форматов."""

    signals: np.ndarray                 # [12, N] в мВ, канонический порядок
    sampling_rate: int
    speed: int                          # мм/с
    gain: int                           # мм/мВ
    layout: str                         # "12x1" / "3x4" / ...
    leads: list                         # порядок 12 отведений
    log: list = field(default_factory=list)

    def to_db_record(self) -> dict:
        return {
            "signals": self.signals.tolist(),
            "sampling_rate": self.sampling_rate,
            "speed": self.speed,
            "gain": self.gain,
            "layout": self.layout,
        }
