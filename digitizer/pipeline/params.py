"""Параметры записи ЭКГ, выбираемые пользователем перед оцифровкой."""
from __future__ import annotations

from dataclasses import dataclass

# Формат -> (шаблон раскладки ecg_layout, число строк сетки, число колонок).
LAYOUT_SPECS: dict[str, dict] = {
    "3x4": {"template": "standard_3x4", "rows": 3, "cols": 4, "rhythm": True},
    "3x4_no_rhythm": {"template": "standard_3x4_no_rhythm", "rows": 3, "cols": 4, "rhythm": False},
    "6x2": {"template": "standard_6x2", "rows": 6, "cols": 2, "rhythm": False},
    "12x1": {"template": "standard_12x1", "rows": 12, "cols": 1, "rhythm": False},
}


@dataclass
class ECGParams:
    """Параметры оцифровки. speed — мм/с, gain — мм/мВ."""

    layout: str = "3x4"          # 3x4 / 6x2 / 12x1 / ...
    speed: int = 25              # мм/с (25 или 50)
    gain: int = 10               # мм/мВ (5, 10 или 20)
    sampling_rate: int = 500     # Гц итогового сигнала
    duration_s: float = 10.0     # длительность записи, сек

    def spec(self) -> dict:
        if self.layout not in LAYOUT_SPECS:
            raise ValueError(
                f"Неизвестный формат '{self.layout}'. Доступны: {list(LAYOUT_SPECS)}"
            )
        return LAYOUT_SPECS[self.layout]

    @property
    def n_samples(self) -> int:
        return int(round(self.sampling_rate * self.duration_s))

    def to_metadata(self) -> dict:
        return {
            "sampling_rate": self.sampling_rate,
            "speed": self.speed,
            "gain": self.gain,
            "layout": self.layout,
        }
