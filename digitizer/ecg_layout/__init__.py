"""ecg_layout — распознавание раскладки ЭКГ по подписям отведений.

Идея: не угадывать раскладку по жёсткому шаблону (как делают Open-ECG-Digitizer
и победитель PhysioNet 2024), а ПРОЧИТАТЬ подписи отведений (I, II, aVR, V1…)
и по их положению на картинке восстановить сетку: какое отведение в какой
клетке и какому отрезку времени оно соответствует.

Публичный вход — функция detect_layout из модуля detect.
"""
from ecg_layout.types import LayoutMap, LeadCell, LeadLabel, TextDetection

__all__ = ["LayoutMap", "LeadCell", "LeadLabel", "TextDetection"]
