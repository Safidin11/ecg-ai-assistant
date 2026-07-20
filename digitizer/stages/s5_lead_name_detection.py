"""Этап 5 — Lead name detection: найти подписи отведений (OCR).

По статье подписи отведений дают ГОРИЗОНТАЛЬНЫЕ якоря (начало каждой колонки).
Здесь только находим подписи и их позиции; сами границы колонок — в s6.

OCR запускаем на очищенном изображении (после s1) и сопоставляем текст с закрытым
словарём из 12 имён (ошибки OCR чинятся, мусор отсеивается). Правится независимо.
"""
from __future__ import annotations

from PIL import ImageDraw

from ecg_layout.matching import match_text_to_lead
from ecg_layout.preprocess import mask_to_image
from stages.context import StageContext

NAME = "s5_lead_name_detection"

_reader = None


def _ocr():
    global _reader
    if _reader is None:
        from ecg_layout.ocr import EasyOCRBackend
        _reader = EasyOCRBackend()
    return _reader


def run(ctx: StageContext, ocr=None) -> StageContext:
    backend = ocr or _ocr()
    dets = backend.detect_image(mask_to_image(ctx.ink_mask))

    labels: list[dict] = []
    for d in dets:
        lead, score = match_text_to_lead(d.text)
        if lead is not None:
            labels.append({
                "lead": lead, "cx": d.cx, "cy": d.cy,
                "bbox": (d.x, d.y, d.w, d.h),
            })
    ctx.lead_labels = labels
    found = sorted({lb["lead"] for lb in labels})
    ctx.note(f"{NAME}: подписей {len(labels)} ({len(found)} уник.): {found}")
    return ctx


def visualize(ctx: StageContext):
    img = mask_to_image(ctx.ink_mask).convert("RGB")
    draw = ImageDraw.Draw(img)
    for lb in ctx.lead_labels or []:
        x, y, w, h = lb["bbox"]
        draw.rectangle([x, y, x + w, y + h], outline=(30, 110, 230), width=2)
        draw.text((x, max(0, y - 12)), lb["lead"], fill=(30, 110, 230))
    return img
