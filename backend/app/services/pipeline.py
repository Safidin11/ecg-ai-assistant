"""Оркестратор пайплайна: связывает вместе все блоки.

Один вызов process_upload проводит загруженную картинку через весь путь:
    картинка -> дигитайзер -> сигнал -> БД(recording) -> модель -> БД(prediction)

Здесь нет "умной" логики самих блоков — только их последовательный вызов.
Это удобная точка, где потом заглушки заменятся на реальные компоненты.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Prediction, Recording
from app.services import diagnosis_service, digitizer_service, storage


def process_upload(
    db: Session,
    image_bytes: bytes,
    filename: str,
    notes: str | None = None,
) -> tuple[Recording, Prediction]:
    """Проводит одну картинку ЭКГ через весь пайплайн и сохраняет результат в БД."""

    # 1. Сохраняем исходную картинку на диск
    image_path = storage.save_image(image_bytes, filename)

    # 2. Дигитайзер: картинка -> сигнал [12, N]
    digitized = digitizer_service.digitize(image_path)

    # 3. Сохраняем сигнал на диск
    signal_path = storage.save_signal(digitized.signal)

    # 4. Пишем запись в БД (таблица recordings)
    recording = Recording(
        image_path=image_path,
        signal_path=signal_path,
        sampling_rate=digitized.sampling_rate,
        duration=digitized.duration,
        quality_score=digitized.quality_score,
        notes=notes,
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    # 5. Модель диагностики: сигнал -> вероятности
    predicted = diagnosis_service.predict(digitized.signal)

    # 6. Пишем предсказание в БД (таблица predictions)
    prediction = Prediction(
        recording_id=recording.id,
        model_version=predicted.model_version,
        probabilities=predicted.probabilities,
        diagnosis=predicted.diagnosis,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return recording, prediction
