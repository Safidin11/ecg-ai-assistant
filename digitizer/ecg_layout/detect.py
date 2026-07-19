"""Связка распознавания раскладки + командная строка.

detect_layout — публичная функция: картинка -> LayoutMap.
main — запуск из терминала для проверки на реальной картинке.
"""
from __future__ import annotations

import argparse
import json

from ecg_layout.baselines import detect_n_rows, standard_format_from_rows
from ecg_layout.complete import assemble_from_format, complete_layout
from ecg_layout.infer import infer_layout
from ecg_layout.matching import match_text_to_lead
from ecg_layout.ocr import OCRBackend
from ecg_layout.preprocess import mask_to_image, remove_grid
from ecg_layout.templates import build_layout_from_template
from ecg_layout.types import LayoutMap, LeadLabel

# Синонимы форматов для ручного override.
_OVERRIDE_TO_TEMPLATE = {
    "3x4": "standard_3x4",
    "3x4_rhythm": "standard_3x4",
    "3x4_no_rhythm": "standard_3x4_no_rhythm",
    "6x2": "standard_6x2",
    "12x1": "standard_12x1",
}


def _image_size(image_path: str) -> tuple[int, int]:
    """Размер картинки (ширина, высота) через Pillow."""
    from PIL import Image

    with Image.open(image_path) as im:
        return im.width, im.height


def _resolve_override(value: str) -> str:
    """Приводит ручной формат ('3x4', '12x1'…) к имени шаблона."""
    key = value.strip().lower()
    if key in _OVERRIDE_TO_TEMPLATE:
        return _OVERRIDE_TO_TEMPLATE[key]
    return value  # уже имя шаблона


def _match_labels(detections):
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
    return labels, unmatched


def detect_layout(
    image_path: str,
    ocr: OCRBackend,
    total_seconds: float = 10.0,
    image_size: tuple[int, int] | None = None,
    fallback_template: str = "standard_3x4",
    min_leads: int = 8,
    complete: bool = True,
    layout_override: str | None = None,
    use_grid_removal: bool = True,
) -> LayoutMap:
    """Картинка -> раскладка ЭКГ.

    Порядок определения формата:
      1. layout_override ('3x4' / '6x2' / '12x1') — если задан вручную.
      2. Число строк по сигналу (удаляем сетку -> считаем полосы отведений).
         Формат почти однозначно следует из числа строк.
      3. Иначе — инференс по подписям OCR (+ достройка).

    В поле layout.source видно, как определён формат. Прочитанные OCR отведения
    помечены inferred=False, достроенные по формату — inferred=True.
    """
    if image_size is None:
        image_size = _image_size(image_path)
    width, height = image_size

    # 1. Препроцессинг: убираем сетку -> чище OCR + считаем строки по сигналу.
    n_rows = None
    detections = None
    if use_grid_removal:
        try:
            mask = remove_grid(image_path)
            detections = ocr.detect_image(mask_to_image(mask))
            n_rows = detect_n_rows(mask)
        except Exception:
            detections = None
    if detections is None:
        detections = ocr.detect(image_path)

    labels, unmatched = _match_labels(detections)
    ocr_matched = sorted({lb.lead for lb in labels})

    # 2. Формат: override -> по строкам -> иначе инференс по подписям.
    template = None
    source_prefix = ""
    if layout_override:
        template = _resolve_override(layout_override)
        source_prefix = "override:"
    elif n_rows is not None:
        template = standard_format_from_rows(n_rows)["template"]
        source_prefix = f"baseline({n_rows}rows):"

    if template is not None:
        layout = assemble_from_format(template, width, height, total_seconds, labels)
        layout.unmatched = unmatched
        layout.source = f"{source_prefix}{template}"
        return layout

    # 3. Нет ни override, ни строк -> старый путь по подписям.
    layout = infer_layout(labels, image_w=width, image_h=height, total_seconds=total_seconds)
    if len(layout.leads_found) >= min_leads:
        layout.source = "ocr"
        layout.unmatched = unmatched
        layout.ocr_matched_leads = ocr_matched
        if complete:
            layout = complete_layout(layout, width, height)
        return layout

    fallback = build_layout_from_template(fallback_template, width, height, total_seconds)
    fallback.unmatched = unmatched
    fallback.ocr_matched_leads = ocr_matched
    return fallback


def draw_overlay(image_path: str, layout: LayoutMap, out_path: str) -> None:
    """Рисует поверх картинки рамки подписей и назначенные отведения/время."""
    from PIL import Image, ImageDraw

    im = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    for cell in layout.cells:
        x, y, w, h = cell.bbox
        if cell.inferred:
            color = (20, 160, 60)      # зелёный — достроено по шаблону
        elif cell.is_rhythm:
            color = (220, 40, 40)      # красный — ритм-полоса
        else:
            color = (30, 110, 230)     # синий — прочитано OCR
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
    parser.add_argument("--layout", default=None,
                        help="задать формат вручную: 3x4 / 6x2 / 12x1 (иначе определяется сам)")
    parser.add_argument("--no-grid-removal", action="store_true",
                        help="не удалять сетку и не определять формат по сигналу")
    args = parser.parse_args()

    from ecg_layout.ocr import EasyOCRBackend

    ocr = EasyOCRBackend(gpu=args.gpu)
    layout = detect_layout(
        args.image, ocr=ocr, total_seconds=args.seconds,
        fallback_template=args.fallback, min_leads=args.min_leads,
        layout_override=args.layout, use_grid_removal=not args.no_grid_removal,
    )

    print(f"Источник раскладки: {layout.source}")
    n_ocr = len(layout.ocr_matched_leads)
    print(f"OCR реально прочитал: {', '.join(layout.ocr_matched_leads) or '—'} ({n_ocr}/12)")
    print(f"Раскладка: {layout.n_rows} строк x {layout.n_cols} колонок")
    inferred = sorted({c.lead for c in layout.cells if c.inferred})
    if inferred:
        print(f"Достроено по шаблону: {', '.join(inferred)}")
    print(f"Итоговые отведения: {', '.join(layout.leads_found) or '—'}")
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
