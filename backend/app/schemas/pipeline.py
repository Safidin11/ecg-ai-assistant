from pydantic import BaseModel

from app.schemas.prediction import PredictionRead
from app.schemas.recording import RecordingRead


class UploadResponse(BaseModel):
    """Ответ на загрузку ЭКГ: запись, предсказание, чистая ЭКГ и уверенность."""

    recording: RecordingRead
    prediction: PredictionRead
    render_url: str          # URL заново отрисованной чистой ЭКГ
    confidence: float        # уверенность топ-диагноза (0..1)
