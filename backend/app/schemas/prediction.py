from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionBase(BaseModel):
    model_version: str
    probabilities: dict[str, float]
    diagnosis: str


class PredictionCreate(PredictionBase):
    recording_id: int


class PredictionRead(PredictionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recording_id: int
    created_at: datetime
