from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.recordings import router as recordings_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# noqa: чтобы модели зарегистрировались в Base.metadata до create_all
from app.db import models  # noqa: F401

app = FastAPI(
    title="ECG AI Assistant",
    description="Учебный ИИ-помощник для распознавания ЭКГ. Не медицинское изделие.",
    version="0.1.0",
)

# Разрешаем запросы с любого источника (для разработки).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recordings_router)


@app.on_event("startup")
def on_startup() -> None:
    # создаём папки под данные, чтобы сохранение файлов не падало
    Path(settings.images_storage_path).mkdir(parents=True, exist_ok=True)
    Path(settings.signals_storage_path).mkdir(parents=True, exist_ok=True)
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and db_path != settings.database_url:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    # создаём таблицы БД, если их ещё нет
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Отдаём фронтенд (frontend/index.html) прямо из приложения по адресу "/".
# Монтируем ПОСЛЕ API-роутов, чтобы /health и /recordings имели приоритет.
_frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
