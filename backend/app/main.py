from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine

# noqa: чтобы модели зарегистрировались в Base.metadata до create_all
from app.db import models  # noqa: F401

app = FastAPI(
    title="ECG AI Assistant",
    description="Учебный ИИ-помощник для распознавания ЭКГ. Не медицинское изделие.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
