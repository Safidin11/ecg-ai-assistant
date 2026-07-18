"""OCR-бэкенды: превращают картинку в список найденных кусков текста.

Бэкенд — сменная "голова". Логика инференса раскладки от конкретного OCR не
зависит, поэтому движок можно менять (EasyOCR, PaddleOCR, Tesseract…), не
трогая остальной код.
"""
from __future__ import annotations

from typing import Protocol

from ecg_layout.types import TextDetection


class OCRBackend(Protocol):
    """Любой OCR должен уметь одно: по пути к картинке вернуть куски текста."""

    def detect(self, image_path: str) -> list[TextDetection]:
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


class EasyOCRBackend:
    """Реальный OCR на базе EasyOCR (нейросетевой, качественнее Tesseract).

    Тяжёлая зависимость (тянет torch), поэтому импортируется лениво — только
    когда бэкенд реально создаётся.
    """

    def __init__(self, languages: list[str] | None = None, gpu: bool = False):
        import easyocr  # ленивый импорт

        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu)

    def detect(self, image_path: str) -> list[TextDetection]:
        # readtext возвращает [(bbox_из_4_точек, текст, уверенность), ...]
        results = self._reader.readtext(image_path)
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
