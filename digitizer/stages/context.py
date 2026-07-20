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

    log: list[str] = field(default_factory=list)

    def note(self, msg: str) -> None:
        self.log.append(msg)
