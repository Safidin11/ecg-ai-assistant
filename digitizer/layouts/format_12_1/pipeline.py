"""Пайплайн 12×1 = вызов эталонных этапов stages/ (s1..s10), без их изменения."""
from __future__ import annotations

from layouts.common.leads import CANONICAL_LEADS
from layouts.common.types import DigitizeResult

# Эталонные этапы. Импортируем и вызываем — НЕ модифицируем.
from stages import (
    s1_preprocess, s2_baseline_detection, s3_configuration, s4_vertical_anchors,
    s5_lead_name_detection, s6_horizontal_anchors, s7_lead_crop,
    s8_signal_extraction, s9_calibration, s10_assemble,
)
from stages.context import StageContext

_STAGES = [
    s1_preprocess, s2_baseline_detection, s3_configuration, s4_vertical_anchors,
    s5_lead_name_detection, s6_horizontal_anchors, s7_lead_crop,
    s8_signal_extraction, s9_calibration, s10_assemble,
]


def run(image_path: str, config=None) -> DigitizeResult:
    """Оцифровка фото формата 12×1 через эталонный пайплайн."""
    ctx = StageContext(image_path=image_path)
    if config is not None:
        ctx.speed = getattr(config, "speed", ctx.speed)
        ctx.gain = getattr(config, "gain", ctx.gain)
        ctx.sampling_rate = getattr(config, "sampling_rate", ctx.sampling_rate)
        ctx.duration_s = getattr(config, "duration_s", ctx.duration_s)
    for stage in _STAGES:
        ctx = stage.run(ctx)
    return DigitizeResult(
        signals=ctx.signal_matrix,
        sampling_rate=ctx.sampling_rate,
        speed=ctx.speed,
        gain=ctx.gain,
        layout="12x1",
        leads=list(CANONICAL_LEADS),
        log=ctx.log,
    )
