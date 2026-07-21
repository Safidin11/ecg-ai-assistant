"""Общая отрисовка чистой ЭКГ из сигнала [12, N].

Обёртка над проверенным рендером (pipeline.render) — переиспользуем, не трогая.
"""
from __future__ import annotations

import numpy as np


def render(signals: np.ndarray, layout: str, speed: int, gain: int,
           sampling_rate: int, out_path: str, duration_s: float = 10.0) -> str:
    from pipeline import ECGParams
    from pipeline.render import render_ecg

    params = ECGParams(layout=layout, speed=speed, gain=gain,
                       sampling_rate=sampling_rate, duration_s=duration_s)
    return render_ecg(signals, params, out_path)
