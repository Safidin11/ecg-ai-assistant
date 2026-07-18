from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecordingBase(BaseModel):
    image_path: str
    signal_path: str
    sampling_rate: int
    duration: float
    quality_score: float | None = None
    notes: str | None = None


class RecordingCreate(RecordingBase):
    """Схема для создания записи (после работы дигитайзера)"""


class RecordingRead(RecordingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
