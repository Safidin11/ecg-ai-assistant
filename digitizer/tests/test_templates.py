"""Тесты шаблонов раскладок и отката OCR -> шаблон."""
from ecg_layout.detect import detect_layout
from ecg_layout.ocr import FakeOCRBackend
from ecg_layout.templates import available_templates, build_layout_from_template
from ecg_layout.types import TextDetection


def test_template_3x4_leads_and_time():
    layout = build_layout_from_template("standard_3x4", 1200, 1000)
    assert layout.source == "template:standard_3x4"
    assert layout.n_cols == 4
    # 12 отведений сетки + 1 ритм-полоса
    assert len(layout.cells) == 13
    # V4 в колонке 3 -> 7.5..10 с
    v4 = [c for c in layout.cells if c.lead == "V4"][0]
    assert v4.col == 3
    assert abs(v4.time_offset_s - 7.5) < 1e-6
    # ритм-полоса II на все 10 с
    rhythm = [c for c in layout.cells if c.is_rhythm][0]
    assert rhythm.lead == "II"
    assert abs(rhythm.duration_s - 10.0) < 1e-6


def test_template_6x2_and_12x1_shapes():
    l6 = build_layout_from_template("standard_6x2", 1000, 1200)
    assert l6.n_cols == 2 and l6.n_rows == 6 and len(l6.cells) == 12
    l12 = build_layout_from_template("standard_12x1", 800, 1300)
    assert l12.n_cols == 1 and l12.n_rows == 12 and len(l12.cells) == 12


def test_all_templates_cover_12_leads():
    for name in available_templates():
        layout = build_layout_from_template(name, 1000, 1000)
        grid_leads = {c.lead for c in layout.cells if not c.is_rhythm}
        assert grid_leads == {
            "I", "II", "III", "aVR", "aVL", "aVF",
            "V1", "V2", "V3", "V4", "V5", "V6",
        }


def test_fallback_when_ocr_finds_nothing():
    # OCR вернул только мусор -> должен сработать откат на шаблон
    junk = [TextDetection("25mm/s", 10, 10, 40, 12), TextDetection("Ivanov", 10, 40, 60, 12)]
    layout = detect_layout(
        "x.png", ocr=FakeOCRBackend(junk), image_size=(1200, 1000),
        fallback_template="standard_3x4",
    )
    assert layout.source == "template:standard_3x4"
    assert len(layout.leads_found) == 12


def test_ocr_used_when_enough_labels():
    # OCR нашёл все 12 подписей -> доверяем OCR, шаблон не нужен
    grid = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]
    rows_y, cols_x = [200, 500, 800], [100, 400, 700, 1000]
    dets = []
    for r, leads in enumerate(grid):
        for c, t in enumerate(leads):
            dets.append(TextDetection(t, cols_x[c] - 10, rows_y[r] - 6, 20, 12))
    layout = detect_layout("x.png", ocr=FakeOCRBackend(dets), image_size=(1200, 1000))
    assert layout.source == "ocr"
    assert len(layout.leads_found) == 12
