"""Сервис хранилища файлов.

Отвечает за сохранение исходных изображений ЭКГ и оцифрованных сигналов
на диск. В БД потом кладётся только путь к файлу (см. PROJECT.md).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np

from app.core.config import settings


def _ensure_dir(path: str) -> Path:
    """Создаёт папку, если её ещё нет, и возвращает Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_image(content: bytes, original_filename: str) -> str:
    """Сохраняет загруженную картинку ЭКГ на диск.

    Возвращает путь к сохранённому файлу.
    """
    images_dir = _ensure_dir(settings.images_storage_path)
    # сохраняем расширение исходного файла (.jpg/.png/...), имя делаем уникальным
    suffix = Path(original_filename).suffix or ".bin"
    filename = f"{uuid.uuid4().hex}{suffix}"
    file_path = images_dir / filename
    file_path.write_bytes(content)
    return str(file_path)


def save_signal(signal: np.ndarray) -> str:
    """Сохраняет сигнал (массив [12, N]) на диск в формате .npy.

    Возвращает путь к сохранённому файлу.
    """
    signals_dir = _ensure_dir(settings.signals_storage_path)
    filename = f"{uuid.uuid4().hex}.npy"
    file_path = signals_dir / filename
    np.save(file_path, signal)
    return str(file_path)


def load_signal(signal_path: str) -> np.ndarray:
    """Загружает сигнал обратно с диска."""
    return np.load(signal_path)
