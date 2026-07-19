"""Базовый класс этапа пайплайна.

Один этап = одна задача. Он получает контекст, что-то в нём заполняет и
возвращает его же. Новый этап добавляется как ещё один подкласс Stage — без
изменения остальных.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from pipeline.context import DigitizeContext


class Stage(ABC):
    """Абстрактный этап пайплайна."""

    #: короткое имя этапа (для логов)
    name: str = "stage"

    @abstractmethod
    def run(self, ctx: DigitizeContext) -> DigitizeContext:
        """Выполнить этап над контекстом и вернуть его."""
        raise NotImplementedError
