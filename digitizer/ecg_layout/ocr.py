"""OCR-бэкенды: превращают картинку в список найденных кусков текста.

Бэкенд — сменная "голова". Логика инференса раскладки от конкретного OCR не
зависит, поэтому движок можно менять (EasyOCR, PaddleOCR, Tesseract…), не
трогая остальной код.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np

from ecg_layout.types import TextDetection


class OCRBackend(Protocol):
    """Любой OCR должен уметь: по пути к картинке или по картинке в памяти
    вернуть куски текста."""

    def detect(self, image_path: str) -> list[TextDetection]:
        ...

    def detect_image(self, image) -> list[TextDetection]:
        ...


class FakeOCRBackend:
    """Заглушка для тестов: возвращает заранее заданные детекции.

    Позволяет проверять инференс раскладки без реальной картинки и без
    установки тяжёлого OCR.
    """

    def __init__(self, detections: list[TextDetection]):
        self._detections = detections

    def detect(self, image_path: str) -> list[TextDetection]:
        return list(self._detections)

    def detect_image(self, image) -> list[TextDetection]:
        return list(self._detections)


class EasyOCRBackend:
    """Реальный OCR на базе EasyOCR (нейросетевой, качественнее Tesseract).

    Тяжёлая зависимость (тянет torch), поэтому импортируется лениво — только
    когда бэкенд реально создаётся.
    """

    # Настройки, подобранные на реальных ЭКГ: увеличение картинки и повышенная
    # чувствительность помогают читать мелкие/тонкие подписи отведений.
    _READ_PARAMS = dict(mag_ratio=2.0, min_size=3, text_threshold=0.4, low_text=0.3)

    def __init__(self, languages: list[str] | None = None, gpu: bool = False):
        import easyocr  # ленивый импорт

        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu)

    def _parse(self, results) -> list[TextDetection]:
        detections: list[TextDetection] = []
        for box, text, conf in results:
            xs = [float(p[0]) for p in box]
            ys = [float(p[1]) for p in box]
            x, y = min(xs), min(ys)
            w, h = max(xs) - x, max(ys) - y
            detections.append(
                TextDetection(text=text, x=x, y=y, w=w, h=h, conf=float(conf))
            )
        return detections

    def detect(self, image_path: str) -> list[TextDetection]:
        return self._parse(self._reader.readtext(image_path, **self._READ_PARAMS))

    def detect_image(self, image) -> list[TextDetection]:
        """OCR для картинки в памяти (PIL.Image или numpy-массив)."""
        arr = np.asarray(image)
        return self._parse(self._reader.readtext(arr, **self._READ_PARAMS))
