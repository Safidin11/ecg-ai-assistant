from pydantic import BaseModel

from app.schemas.prediction import PredictionRead
from app.schemas.recording import RecordingRead


class UploadResponse(BaseModel):
    """Ответ на загрузку ЭКГ: сохранённая запись + сделанное предсказание."""

    recording: RecordingRead
    prediction: PredictionRead
