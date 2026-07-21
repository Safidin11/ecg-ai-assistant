"""Конфигурация формата 3×4: фиксированная геометрия и порядок отведений."""
from __future__ import annotations

from dataclasses import dataclass

N_ROWS = 3          # три строки сетки
N_COLS = 4          # четыре колонки
RHYTHM_LEAD = "II"  # нижняя ритм-полоса

# Стандартная раскладка 3×4: (строка, колонка) -> отведение.
CELL_MAP: dict[tuple[int, int], str] = {
    (0, 0): "I",   (0, 1): "aVR", (0, 2): "V1", (0, 3): "V4",
    (1, 0): "II",  (1, 1): "aVL", (1, 2): "V2", (1, 3): "V5",
    (2, 0): "III", (2, 1): "aVF", (2, 2): "V3", (2, 3): "V6",
}


@dataclass
class Config:
    speed: int = 25            # мм/с
    gain: int = 10             # мм/мВ
    sampling_rate: int = 500   # Гц
    duration_s: float = 10.0   # полная длительность записи
    layout: str = "3x4"

    @property
    def col_seconds(self) -> float:
        return self.duration_s / N_COLS      # 2.5 с на колонку

    @property
    def n_samples(self) -> int:
        return int(round(self.sampling_rate * self.duration_s))
