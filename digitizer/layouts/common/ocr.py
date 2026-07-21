"""Общий OCR подписей отведений + сопоставление с закрытым словарём.

Обёртка над проверенными ecg_layout.ocr / ecg_layout.matching.
"""
from __future__ import annotations

from ecg_layout.matching import match_text_to_lead  # noqa: F401 (реэкспорт)

_reader = None


def get_reader(gpu: bool = False):
    global _reader
    if _reader is None:
        from ecg_layout.ocr import EasyOCRBackend
        _reader = EasyOCRBackend(gpu=gpu)
    return _reader


def detect_lead_labels(mask_or_image) -> list[dict]:
    """OCR по картинке (маска/PIL) -> список {lead, cx, cy, bbox} для подписей."""
    from layouts.common.image import mask_to_image

    import numpy as np

    img = mask_to_image(mask_or_image) if isinstance(mask_or_image, np.ndarray) else mask_or_image
    dets = get_reader().detect_image(img)
    labels: list[dict] = []
    for d in dets:
        lead, _ = match_text_to_lead(d.text)
        if lead is not None:
            labels.append({"lead": lead, "cx": d.cx, "cy": d.cy,
                           "bbox": (d.x, d.y, d.w, d.h)})
    return labels
