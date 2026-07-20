"""Контекст, проходящий через все этапы. Каждый этап дописывает свои поля."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class StageContext:
    image_path: str

    # s1 preprocess
    rgb: np.ndarray | None = None
    ink_mask: np.ndarray | None = None          # True = чернила (сигнал/текст)

    # s2 baseline_detection
    bands: list[tuple[int, int]] | None = None   # (y0, y1) вертикальный диапазон каждой строки
    baselines: list[int] | None = None           # y изолинии каждой строки

    # s3 configuration
    n_rows: int | None = None

    # s4 vertical_anchors
    row_bounds: list[tuple[int, int]] | None = None  # (верх, низ) каждого отведения

    # s5 lead_name_detection
    lead_labels: list[dict] | None = None            # [{lead, cx, cy, bbox}]

    # s6 horizontal_anchors
    col_bounds: list[tuple[int, int]] | None = None  # (лево, право) каждой колонки

    # параметры записи (для калибровки); по умолчанию — самые частые
    speed: int = 25          # мм/с
    gain: int = 10           # мм/мВ
    duration_s: float = 10.0
    sampling_rate: int = 500

    # s7 lead_crop
    cells: list[dict] | None = None                  # [{row, col, box, baseline}]
    # s8 signal_extraction
    cell_signals: dict | None = None                 # (row, col) -> отклонение в пикселях
    # s9 calibration
    px_per_s: float | None = None
    px_per_mv: float | None = None
    # s10 assemble
    signal_matrix: np.ndarray | None = None          # [12, N] в мВ

    log: list[str] = field(default_factory=list)

    def note(self, msg: str) -> None:
        self.log.append(msg)
