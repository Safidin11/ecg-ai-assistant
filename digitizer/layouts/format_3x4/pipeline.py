"""Пайплайн формата 3×4: фото -> [12, N] мВ + метаданные.

Оркестрирует специализированные этапы 3×4 поверх общих кирпичей common/.
Полностью независим от 12×1.
"""
from __future__ import annotations

import numpy as np

from layouts.common import ocr
from layouts.common.calibration import calibrate
from layouts.common.image import binarize, load_rgb
from layouts.common.leads import CANONICAL_LEADS, LEAD_TO_INDEX
from layouts.common.signal import resample
from layouts.common.types import DigitizeResult
from layouts.format_3x4 import detector, lead_splitter, signal_extractor
from layouts.format_3x4.config import Config


def run(image_path: str, config: Config | None = None) -> DigitizeResult:
    cfg = config or Config()
    log: list[str] = []

    # 1. препроцессинг (общий): бинаризация/удаление сетки
    mask = binarize(load_rgb(image_path))
    log.append(f"preprocess: маска {mask.shape}, чернил {mask.mean() * 100:.1f}%")

    # 2. подписи отведений (общий OCR) — для колонок и обрезки
    labels = ocr.detect_lead_labels(mask)
    log.append(f"lead names: {sorted({l['lead'] for l in labels})}")

    # 3. детектор 3×4: обрезка листа, строки, колонки
    layout = detector.detect(mask, labels)
    log.append(f"detect: строк {len(layout.row_bands)}, колонок {len(layout.col_bounds)}, "
               f"content {layout.content}")

    # 4. нарезка клеток
    cells = lead_splitter.split(mask, layout, labels, cfg)
    log.append(f"split: клеток {len(cells)}")

    # 5. калибровка (по ширине содержимого)
    x0, _, x1, _ = layout.content
    cal = calibrate(x1 - x0, cfg.duration_s, cfg.speed, cfg.gain)
    log.append(f"calibrate: px_per_s={cal.px_per_s:.1f}, px_per_mV={cal.px_per_mv:.1f}")

    # 6. извлечение сигнала (общий трекинг)
    cell_dev = signal_extractor.extract(mask, cells)

    # 7. сборка [12, N]
    n_total = cfg.n_samples
    matrix = np.zeros((12, n_total), dtype=np.float32)
    seg_n = max(1, int(round(cfg.col_seconds * cfg.sampling_rate)))
    for cell in cells:
        if cell.is_rhythm or cell.lead not in LEAD_TO_INDEX:
            continue
        mv = cell_dev[(cell.row, cell.col)] / (cal.px_per_mv or 1.0)
        seg = resample(mv, seg_n)
        start = int(round(cell.time_offset_s * cfg.sampling_rate))
        end = min(n_total, start + seg_n)
        matrix[LEAD_TO_INDEX[cell.lead], start:end] = seg[: end - start]

    covered = int(np.count_nonzero(matrix.any(axis=1)))
    log.append(f"assemble: [12, {n_total}], отведений с данными {covered}/12")

    return DigitizeResult(
        signals=matrix, sampling_rate=cfg.sampling_rate, speed=cfg.speed,
        gain=cfg.gain, layout="3x4", leads=list(CANONICAL_LEADS), log=log,
    )
