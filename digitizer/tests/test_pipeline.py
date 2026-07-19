"""Тесты модульного пайплайна оцифровки."""
import os
import tempfile

import numpy as np
from PIL import Image, ImageDraw

from pipeline import ECGParams, digitize
from pipeline.digitize import default_stages
from pipeline.render import render_ecg
from pipeline.runner import Pipeline


def _synthetic_12x1(path, h=1200, w=1000):
    """12 чёрных кривых на белом фоне — синтетическая 12×1 ЭКГ."""
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    xs = np.arange(w)
    for i in range(12):
        cy = (i + 0.5) * h / 12
        ys = cy - 25 * np.sin(2 * np.pi * xs / 80)
        draw.line(list(zip(xs.tolist(), ys.tolist())), fill="black", width=2)
    img.save(path)


def test_pipeline_produces_all_12_leads():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "ecg.png")
        _synthetic_12x1(p)
        out = digitize(p, ECGParams(layout="12x1", speed=25, gain=10, sampling_rate=500))
        assert out.signals.shape == (12, 5000)
        nonzero = int(np.count_nonzero(out.signals.any(axis=1)))
        assert nonzero == 12
        assert np.isfinite(out.signals).all()


def test_params_calibration_and_metadata():
    params = ECGParams(layout="3x4", speed=25, gain=10, sampling_rate=500)
    assert params.n_samples == 5000
    assert params.to_metadata() == {
        "sampling_rate": 500, "speed": 25, "gain": 10, "layout": "3x4",
    }


def test_stages_are_ordered_and_replaceable():
    names = Pipeline(default_stages()).stage_names()
    assert names[0] == "preprocess"
    assert names[-1] == "normalize"
    assert "extract" in names and "layout" in names


def test_db_record_has_only_signal_and_metadata():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "ecg.png")
        _synthetic_12x1(p)
        out = digitize(p, ECGParams(layout="12x1"))
        rec = out.to_db_record()
        assert set(rec.keys()) == {"signals", "sampling_rate", "speed", "gain", "layout"}
        assert "image" not in rec  # изображение в БД не сохраняем


def test_render_creates_clean_image():
    signals = np.zeros((12, 5000), dtype=np.float32)
    signals[1] = 0.5 * np.sin(np.linspace(0, 20 * np.pi, 5000))
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "clean.png")
        render_ecg(signals, ECGParams(layout="12x1"), out_path, px_per_mm=3)
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 1000
