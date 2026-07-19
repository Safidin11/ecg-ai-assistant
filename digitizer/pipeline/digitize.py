"""Оркестратор: собирает этапы в пайплайн и запускает оцифровку.

digitize(image_path, params) -> DigitizeOutput с сигналом [12, N] и метаданными.
Список этапов (DEFAULT_STAGES) можно подменить/дополнить — пайплайн расширяем,
а конкретная реализация оцифровки заменяется без изменений в остальной системе.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ecg_layout.leads import CANONICAL_LEADS
from pipeline.context import DigitizeContext
from pipeline.params import ECGParams
from pipeline.runner import Pipeline
from pipeline.stages.crop import CropStage
from pipeline.stages.extract import ExtractStage
from pipeline.stages.grid import GridStage
from pipeline.stages.layout import LayoutStage
from pipeline.stages.normalize import NormalizeStage
from pipeline.stages.perspective import PerspectiveStage
from pipeline.stages.preprocess import PreprocessStage
from pipeline.stages.reconstruct import ReconstructStage


def default_stages() -> list:
    """Стандартный набор этапов оцифровки (в порядке выполнения)."""
    return [
        PreprocessStage(),
        PerspectiveStage(),
        CropStage(),
        LayoutStage(),
        GridStage(),
        ExtractStage(),
        ReconstructStage(),
        NormalizeStage(),
    ]


DEFAULT_STAGES = default_stages


@dataclass
class DigitizeOutput:
    """Результат оцифровки: сигнал + параметры (ровно то, что идёт в БД)."""

    signals: np.ndarray            # [12, N] в мВ, канонический порядок отведений
    sampling_rate: int
    speed: int
    gain: int
    layout: str
    leads: list                    # порядок отведений (12 имён)
    log: list                      # лог этапов (для отладки)

    def to_db_record(self) -> dict:
        """Структура для сохранения в БД (без изображения)."""
        return {
            "signals": self.signals.tolist(),
            "sampling_rate": self.sampling_rate,
            "speed": self.speed,
            "gain": self.gain,
            "layout": self.layout,
        }


def digitize(image_path: str, params: ECGParams, stages: list | None = None) -> DigitizeOutput:
    """Полная оцифровка одной фотографии ЭКГ."""
    pipeline = Pipeline(stages or default_stages())
    ctx = pipeline.run(DigitizeContext(image_path=image_path, params=params))
    return DigitizeOutput(
        signals=ctx.signal_matrix,
        sampling_rate=params.sampling_rate,
        speed=params.speed,
        gain=params.gain,
        layout=params.layout,
        leads=list(CANONICAL_LEADS),
        log=ctx.log,
    )
