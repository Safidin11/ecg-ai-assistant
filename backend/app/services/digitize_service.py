"""Мост между бэкендом и дигитайзером (пакет digitizer/pipeline).

Изолирует конкретную реализацию оцифровки: остальной бэкенд знает только эти
функции. Заменить алгоритм дигитайзера = поменять реализацию здесь, не трогая
API/БД/пайплайн бэкенда.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Пакеты дигитайзера лежат в соседней папке digitizer/ (pipeline, ecg_layout).
_DIGITIZER_DIR = Path(__file__).resolve().parents[3] / "digitizer"
if str(_DIGITIZER_DIR) not in sys.path:
    sys.path.insert(0, str(_DIGITIZER_DIR))


@dataclass
class DigitizeResult:
    signals: np.ndarray      # [12, N] в мВ
    sampling_rate: int
    speed: int
    gain: int
    layout: str
    duration: float
    leads: list


def digitize_image(
    image_path: str,
    layout: str = "3x4",
    speed: int = 25,
    gain: int = 10,
    sampling_rate: int = 500,
    duration: float = 10.0,
) -> DigitizeResult:
    """Оцифровывает фото ЭКГ через модульный пайплайн дигитайзера."""
    from pipeline import ECGParams, digitize

    params = ECGParams(
        layout=layout, speed=speed, gain=gain,
        sampling_rate=sampling_rate, duration_s=duration,
    )
    out = digitize(image_path, params)
    return DigitizeResult(
        signals=out.signals,
        sampling_rate=out.sampling_rate,
        speed=out.speed,
        gain=out.gain,
        layout=out.layout,
        duration=duration,
        leads=out.leads,
    )


def render_clean_ecg(signals: np.ndarray, layout: str, speed: int, gain: int,
                     sampling_rate: int, out_path: str) -> str:
    """Рисует чистую ЭКГ из сигнала и сохраняет в out_path."""
    from pipeline import ECGParams
    from pipeline.render import render_ecg

    params = ECGParams(layout=layout, speed=speed, gain=gain, sampling_rate=sampling_rate)
    return render_ecg(signals, params, out_path)
