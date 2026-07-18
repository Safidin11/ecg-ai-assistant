"""Структуры данных для распознавания раскладки ЭКГ."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextDetection:
    """Один кусок текста, найденный OCR на картинке.

    bbox — прямоугольник (x, y, w, h) в пикселях; (cx, cy) — его центр.
    """

    text: str
    x: float
    y: float
    w: float
    h: float
    conf: float = 1.0

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class LeadLabel:
    """Подпись отведения: текст OCR, распознанный как одно из 12 отведений."""

    lead: str            # каноническое имя ("V1", "aVR", ...)
    cx: float            # центр подписи по X, пиксели
    cy: float            # центр подписи по Y, пиксели
    bbox: tuple[float, float, float, float]  # (x, y, w, h)
    conf: float = 1.0
    source_text: str = ""  # что реально распознал OCR (для отладки)


@dataclass
class LeadCell:
    """Одна клетка раскладки: отведение + его место в сетке и во времени."""

    lead: str
    row: int                     # номер строки (0 — сверху)
    col: int                     # номер колонки (0 — слева)
    bbox: tuple[float, float, float, float]
    time_offset_s: float         # с какой секунды записи начинается этот кусок
    duration_s: float            # сколько секунд длится этот кусок
    is_rhythm: bool = False      # True для полноширинной ритм-полосы
    conf: float = 1.0

    def to_dict(self) -> dict:
        return {
            "lead": self.lead,
            "row": self.row,
            "col": self.col,
            "bbox": list(self.bbox),
            "time_offset_s": round(self.time_offset_s, 3),
            "duration_s": round(self.duration_s, 3),
            "is_rhythm": self.is_rhythm,
            "conf": round(self.conf, 3),
        }


@dataclass
class LayoutMap:
    """Итог распознавания раскладки всей картинки."""

    n_rows: int
    n_cols: int
    total_seconds: float
    cells: list[LeadCell] = field(default_factory=list)
    unmatched: list[TextDetection] = field(default_factory=list)

    @property
    def leads_found(self) -> list[str]:
        return sorted({c.lead for c in self.cells})

    def to_dict(self) -> dict:
        return {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "total_seconds": self.total_seconds,
            "leads_found": self.leads_found,
            "cells": [c.to_dict() for c in self.cells],
            "unmatched_texts": [d.text for d in self.unmatched],
        }
