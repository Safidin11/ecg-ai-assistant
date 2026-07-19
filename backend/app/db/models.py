from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recording(Base):
    """Одна оцифрованная ЭКГ: сигнал + параметры записи.

    Изображение в БД НЕ хранится — сохраняется только цифровой сигнал (файлом,
    путь в signal_path) и метаданные (частота, скорость, усиление, формат).
    """

    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signal_path: Mapped[str] = mapped_column(String, nullable=False)
    sampling_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)      # мм/с
    gain: Mapped[int] = mapped_column(Integer, nullable=False)       # мм/мВ
    layout: Mapped[str] = mapped_column(String, nullable=False)      # 3x4 / 6x2 / 12x1
    duration: Mapped[float] = mapped_column(Float, nullable=False)

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="recording", cascade="all, delete-orphan"
    )


class Prediction(Base):
    """Результат работы модели диагностики для конкретной записи"""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recording_id: Mapped[int] = mapped_column(ForeignKey("recordings.id"), nullable=False)

    model_version: Mapped[str] = mapped_column(String, nullable=False)
    probabilities: Mapped[dict] = mapped_column(JSON, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recording: Mapped["Recording"] = relationship(back_populates="predictions")
