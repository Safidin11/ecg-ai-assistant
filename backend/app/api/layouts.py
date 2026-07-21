"""API для новой модульной архитектуры: выбор формата + оцифровка.

Запускает независимый пайплайн выбранного формата (layouts/format_X) в
окружении дигитайзера (там OCR и все зависимости) как подпроцесс.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings

router = APIRouter(prefix="/layouts", tags=["layouts"])

_DIGITIZER = Path(__file__).resolve().parents[3] / "digitizer"
_PY = _DIGITIZER / ".venv" / "bin" / "python"

AVAILABLE_FORMATS = ["12x1", "3x4"]


@router.get("/formats")
def list_formats() -> dict:
    return {"formats": AVAILABLE_FORMATS}


@router.post("/digitize")
def digitize(
    file: UploadFile = File(..., description="Фото ЭКГ"),
    layout: str = Form(..., description="Формат: 12x1 или 3x4"),
) -> dict:
    if layout not in AVAILABLE_FORMATS:
        raise HTTPException(status_code=400, detail=f"Неизвестный формат '{layout}'")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")

    job = uuid.uuid4().hex
    out_dir = (Path(settings.stage_debug_path).resolve()) / f"layouts_{job}"
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "x.png").suffix or ".png"
    fd, tmp_img = tempfile.mkstemp(suffix=suffix, prefix="ecg_layout_")
    with open(fd, "wb") as f:
        f.write(data)

    try:
        proc = subprocess.run(
            [str(_PY), "layouts_run.py", layout, tmp_img, str(out_dir)],
            cwd=str(_DIGITIZER),
            capture_output=True, text=True, timeout=240,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Пайплайн не успел за отведённое время")
    finally:
        if os.path.exists(tmp_img):
            os.remove(tmp_img)

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Пайплайн упал:\n{proc.stderr[-800:]}")

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise HTTPException(status_code=500, detail=f"Не удалось разобрать ответ:\n{proc.stdout[-500:]}")

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    if not (out_dir / "render.png").exists():
        raise HTTPException(status_code=500, detail="Рендер не создан")

    result["render_url"] = f"/stage-debug/layouts_{job}/render.png"
    return result
