"""API-роуты для работы с записями ЭКГ и предсказаниями."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.models import Prediction, Recording
from app.db.session import get_db
from app.schemas.pipeline import UploadResponse
from app.schemas.prediction import PredictionRead
from app.schemas.recording import RecordingRead
from app.services import pipeline

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("", response_model=UploadResponse, status_code=201)
def upload_recording(
    file: UploadFile = File(..., description="Изображение ЭКГ (jpg/png/pdf)"),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Загрузить изображение ЭКГ и прогнать его через весь пайплайн.

    Возвращает созданную запись и предсказание модели.
    """
    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Пустой файл")

    recording, prediction = pipeline.process_upload(
        db=db,
        image_bytes=image_bytes,
        filename=file.filename or "upload.bin",
        notes=notes,
    )
    return UploadResponse(
        recording=RecordingRead.model_validate(recording),
        prediction=PredictionRead.model_validate(prediction),
    )


@router.get("", response_model=list[RecordingRead])
def list_recordings(db: Session = Depends(get_db)) -> list[Recording]:
    """Список всех загруженных записей (новые сверху)."""
    return db.query(Recording).order_by(Recording.id.desc()).all()


@router.get("/{recording_id}", response_model=RecordingRead)
def get_recording(recording_id: int, db: Session = Depends(get_db)) -> Recording:
    """Одна запись по её id."""
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return recording


@router.get("/{recording_id}/predictions", response_model=list[PredictionRead])
def get_recording_predictions(
    recording_id: int, db: Session = Depends(get_db)
) -> list[Prediction]:
    """Все предсказания для конкретной записи (новые сверху)."""
    if db.get(Recording, recording_id) is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return (
        db.query(Prediction)
        .filter(Prediction.recording_id == recording_id)
        .order_by(Prediction.id.desc())
        .all()
    )
