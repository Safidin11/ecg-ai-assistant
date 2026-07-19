"""Сервис хранилища файлов.

Отвечает за сохранение исходных изображений ЭКГ и оцифрованных сигналов
на диск. В БД потом кладётся только путь к файлу (см. PROJECT.md).
"""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import numpy as np

from app.core.config import settings


def _ensure_dir(path: str) -> Path:
    """Создаёт папку, если её ещё нет, и возвращает Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_temp_image(content: bytes, original_filename: str) -> str:
    """Сохраняет загруженную картинку ВРЕМЕННО (для обработки).

    Изображение в проекте не хранится — этот файл нужно удалить после оцифровки.
    """
    suffix = Path(original_filename).suffix or ".bin"
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="ecg_upload_")
    with open(fd, "wb") as f:
        f.write(content)
    return path


def new_render_path() -> tuple[str, str]:
    """Возвращает (полный_путь, имя_файла) для сохранения отрисованной ЭКГ."""
    renders_dir = _ensure_dir(settings.renders_storage_path)
    filename = f"{uuid.uuid4().hex}.png"
    return str(renders_dir / filename), filename


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
