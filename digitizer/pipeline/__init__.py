"""Модульный пайплайн оцифровки ЭКГ.

Фото бумажной ЭКГ + параметры -> цифровой сигнал [12, N] в мВ + метаданные.
Затем по сигналу можно заново отрисовать чистую ЭКГ и поставить диагноз.

Каждый этап — отдельный модуль (stages/), выполняющий одну задачу. Пайплайн
легко расширяется, а конкретный алгоритм оцифровки заменяется без изменения
остальной системы.
"""
from pipeline.context import DigitizeContext
from pipeline.digitize import DEFAULT_STAGES, DigitizeOutput, digitize
from pipeline.params import ECGParams
from pipeline.runner import Pipeline

__all__ = [
    "ECGParams",
    "DigitizeContext",
    "Pipeline",
    "digitize",
    "DigitizeOutput",
    "DEFAULT_STAGES",
]
