"""Связка распознавания раскладки + командная строка.

detect_layout — публичная функция: картинка -> LayoutMap.
main — запуск из терминала для проверки на реальной картинке.
"""
from __future__ import annotations

import argparse
import json

from ecg_layout.infer import infer_layout
from ecg_layout.matching import match_text_to_lead
from ecg_layout.ocr import OCRBackend
from ecg_layout.templates import build_layout_from_template
from ecg_layout.types import LayoutMap, LeadLabel


def _image_size(image_path: str) -> tuple[int, int]:
    """Размер картинки (ширина, высота) через Pillow."""
    from PIL import Image

    with Image.open(image_path) as im:
        return im.width, im.height


def detect_layout(
    image_path: str,
    ocr: OCRBackend,
    total_seconds: float = 10.0,
    image_size: tuple[int, int] | None = None,
    fallback_template: str = "standard_3x4",
    min_leads: int = 8,
) -> LayoutMap:
    """Полный проход: OCR -> отбор подписей -> инференс раскладки.

    Если OCR прочитал < min_leads отведений (подписей нет/плохо распознались),
    откатываемся на известную раскладку fallback_template. В обоих случаях в
    поле layout.source видно, откуда взялся результат.
    """
    detections = ocr.detect(image_path)

    labels: list[LeadLabel] = []
    unmatched = []
    for det in detections:
        lead, score = match_text_to_lead(det.text)
        if lead is None:
            unmatched.append(det)
            continue
        labels.append(
            LeadLabel(
                lead=lead,
                cx=det.cx,
                cy=det.cy,
                bbox=(det.x, det.y, det.w, det.h),
                conf=min(det.conf, score / 100.0),
                source_text=det.text,
            )
        )

    if image_size is None:
        image_size = _image_size(image_path)
    width, height = image_size

    layout = infer_layout(labels, image_w=width, image_h=height, total_seconds=total_seconds)

    # Достаточно ли уверенно прочитали подписи?
    if len(layout.leads_found) >= min_leads:
        layout.source = "ocr"
        layout.unmatched = unmatched
        return layout

    # Иначе — запасной вариант: известный шаблон.
    fallback = build_layout_from_template(fallback_template, width, height, total_seconds)
    fallback.unmatched = unmatched
    return fallback


def draw_overlay(image_path: str, layout: LayoutMap, out_path: str) -> None:
    """Рисует поверх картинки рамки подписей и назначенные отведения/время."""
    from PIL import Image, ImageDraw

    im = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    for cell in layout.cells:
        x, y, w, h = cell.bbox
        color = (220, 40, 40) if cell.is_rhythm else (30, 110, 230)
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        tag = f"{cell.lead} @{cell.time_offset_s:.1f}s"
        draw.text((x, max(0, y - 12)), tag, fill=color)
    im.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Распознавание раскладки ЭКГ по подписям отведений (OCR)."
    )
    parser.add_argument("image", help="путь к картинке ЭКГ")
    parser.add_argument("--seconds", type=float, default=10.0, help="длительность записи, с")
    parser.add_argument("--gpu", action="store_true", help="использовать GPU для OCR")
    parser.add_argument("--json", dest="json_out", help="куда сохранить карту раскладки (JSON)")
    parser.add_argument("--overlay", help="куда сохранить картинку с разметкой")
    parser.add_argument("--fallback", default="standard_3x4",
                        help="шаблон-запасной вариант, если OCR не справился")
    parser.add_argument("--min-leads", type=int, default=8,
                        help="сколько отведений должен прочитать OCR, чтобы ему доверять")
    args = parser.parse_args()

    from ecg_layout.ocr import EasyOCRBackend

    ocr = EasyOCRBackend(gpu=args.gpu)
    layout = detect_layout(
        args.image, ocr=ocr, total_seconds=args.seconds,
        fallback_template=args.fallback, min_leads=args.min_leads,
    )

    print(f"Источник раскладки: {layout.source}")
    print(f"Раскладка: {layout.n_rows} строк x {layout.n_cols} колонок")
    print(f"Найдено отведений: {', '.join(layout.leads_found) or '—'}")
    if layout.unmatched:
        print(f"Не распознано как отведения: {[d.text for d in layout.unmatched]}")
    print()
    for cell in sorted(layout.cells, key=lambda c: (c.row, c.col)):
        mark = " [ритм]" if cell.is_rhythm else ""
        print(
            f"  {cell.lead:>4}  строка {cell.row} колонка {cell.col}  "
            f"t={cell.time_offset_s:.1f}–{cell.time_offset_s + cell.duration_s:.1f}с{mark}"
        )

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(layout.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"\nJSON сохранён: {args.json_out}")

    if args.overlay:
        draw_overlay(args.image, layout, args.overlay)
        print(f"Разметка сохранена: {args.overlay}")


if __name__ == "__main__":
    main()
