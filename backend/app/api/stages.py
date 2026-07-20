"""API для нового поэтапного пайплайна: прогон фото по этапам s1..s6.

Запускает пайплайн дигитайзера (digitizer/stages) в его собственном окружении
(там есть все зависимости, включая OCR) как подпроцесс и отдаёт debug-картинку
каждого этапа. Так на сайте видно результат каждого шага локализации.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings

router = APIRouter(prefix="/stages", tags=["stages"])

_DIGITIZER = Path(__file__).resolve().parents[3] / "digitizer"
_PY = _DIGITIZER / ".venv" / "bin" / "python"


@router.post("/run")
def run_stages(file: UploadFile = File(..., description="Фото ЭКГ")) -> dict:
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")

    job = uuid.uuid4().hex
    # абсолютный путь: подпроцесс запускается из другой папки (digitizer/)
    out_dir = (Path(settings.stage_debug_path).resolve()) / job
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "x.png").suffix or ".png"
    fd, tmp_img = tempfile.mkstemp(suffix=suffix, prefix="ecg_stage_")
    with open(fd, "wb") as f:
        f.write(data)

    try:
        proc = subprocess.run(
            [str(_PY), "-m", "stages.run", tmp_img, str(out_dir)],
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

    # строки лога этапов (вида "sN_...: ...")
    log = [ln.strip() for ln in proc.stdout.splitlines()
           if ln.strip()[:1] == "s" and ln.strip()[1:2].isdigit()]

    images = sorted(out_dir.glob("*.png"))
    stages = [{"name": p.stem, "url": f"/stage-debug/{job}/{p.name}"} for p in images]
    if not stages:
        raise HTTPException(status_code=500, detail="Этапы не дали картинок")
    return {"job": job, "stages": stages, "log": log}
