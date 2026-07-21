"""Общая калибровка: пиксели -> секунды и милливольты.

Полная ширина содержимого = длительность записи. Отсюда:
    px_per_s  = ширина / duration_s
    px_per_mm = px_per_s / speed
    px_per_mV = px_per_mm * gain
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Calibration:
    px_per_s: float
    px_per_mv: float


def calibrate(content_width_px: float, duration_s: float, speed: int, gain: int) -> Calibration:
    w = max(1.0, float(content_width_px))
    px_per_s = w / duration_s
    px_per_mm = px_per_s / speed
    return Calibration(px_per_s=px_per_s, px_per_mv=px_per_mm * gain)
