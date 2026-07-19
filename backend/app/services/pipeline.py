"""Оркестратор пайплайна бэкенда: фото + параметры -> сигнал -> диагноз.

Путь одного запроса:
    фото(врем.) + параметры
      -> дигитайзер (pipeline) -> сигнал [12, N]
      -> сохранить сигнал (файл) + запись в БД (только сигнал+метаданные)
      -> отрисовать ЧИСТУЮ ЭКГ из сигнала (файл для показа)
      -> модель диагностики по СИГНАЛУ -> предсказание в БД
Изображение в БД не сохраняется; временный файл удаляется.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Prediction, Recording
from app.services import diagnosis_service, digitize_service, storage


@dataclass
class ProcessResult:
    recording: Recording
    prediction: Prediction
    render_filename: str          # имя файла отрисованной ЭКГ (для URL /renders/<...>)
    confidence: float             # уверенность топ-диагноза (0..1)


def process_upload(
    db: Session,
    image_bytes: bytes,
    filename: str,
    layout: str = "3x4",
    speed: int = 25,
    gain: int = 10,
    sampling_rate: int = 500,
    notes: str | None = None,
) -> ProcessResult:
    """Проводит фото ЭКГ + параметры через весь пайплайн, сохраняет результат."""

    tmp_image = storage.save_temp_image(image_bytes, filename)
    try:
        # 1. Оцифровка: фото -> сигнал [12, N] в мВ
        digitized = digitize_service.digitize_image(
            tmp_image, layout=layout, speed=speed, gain=gain, sampling_rate=sampling_rate
        )

        # 2. Сохраняем сигнал файлом (в БД — только путь + метаданные)
        signal_path = _save_signal(digitized.signals)

        # 3. Запись в БД: сигнал + метаданные (без изображения)
        recording = Recording(
            signal_path=signal_path,
            sampling_rate=digitized.sampling_rate,
            speed=digitized.speed,
            gain=digitized.gain,
            layout=digitized.layout,
            duration=digitized.duration,
            notes=notes,
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)

        # 4. Рисуем ЧИСТУЮ ЭКГ заново из сигнала (для показа пользователю)
        render_path, render_filename = storage.new_render_path()
        digitize_service.render_clean_ecg(
            digitized.signals, layout=digitized.layout, speed=digitized.speed,
            gain=digitized.gain, sampling_rate=digitized.sampling_rate, out_path=render_path,
        )

        # 5. Диагноз ПО СИГНАЛУ (не по фото)
        predicted = diagnosis_service.predict(digitized.signals)
        prediction = Prediction(
            recording_id=recording.id,
            model_version=predicted.model_version,
            probabilities=predicted.probabilities,
            diagnosis=predicted.diagnosis,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        confidence = float(predicted.probabilities.get(predicted.diagnosis, 0.0))
        return ProcessResult(recording, prediction, render_filename, confidence)
    finally:
        # изображение не храним — удаляем временный файл
        if os.path.exists(tmp_image):
            os.remove(tmp_image)


def _save_signal(signal: np.ndarray) -> str:
    """Сохраняет сигнал [12, N] в .npy в папку сигналов."""
    import uuid
    from pathlib import Path

    d = Path(settings.signals_storage_path)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{uuid.uuid4().hex}.npy"
    np.save(path, signal)
    return str(path)
