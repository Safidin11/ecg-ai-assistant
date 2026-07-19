"""Тесты сборки раскладки из формата и ручного override."""
from ecg_layout.complete import assemble_from_format
from ecg_layout.detect import detect_layout
from ecg_layout.ocr import FakeOCRBackend
from ecg_layout.types import LeadLabel, TextDetection


def _label(lead, cx=100, cy=100):
    return LeadLabel(lead=lead, cx=cx, cy=cy, bbox=(cx, cy, 20, 12), conf=0.9)


def test_assemble_marks_read_vs_inferred():
    read = [_label("aVR"), _label("V2"), _label("V6")]
    layout = assemble_from_format("standard_12x1", 800, 1200, 10.0, read)
    assert layout.n_cols == 1 and len(layout.cells) == 12
    read_cells = {c.lead for c in layout.cells if not c.inferred}
    assert read_cells == {"aVR", "V2", "V6"}
    # остальные достроены
    assert len([c for c in layout.cells if c.inferred]) == 9
    assert layout.source == "format:standard_12x1"


def test_manual_override_forces_format():
    # OCR почти ничего не даёт, но пользователь задал формат вручную
    dets = [TextDetection("aVR", 40, 300, 30, 14), TextDetection("V3", 40, 800, 30, 14)]
    layout = detect_layout(
        "x.png", ocr=FakeOCRBackend(dets), image_size=(800, 1200),
        layout_override="12x1", use_grid_removal=False,
    )
    assert layout.source == "override:standard_12x1"
    assert layout.n_cols == 1
    assert len(layout.leads_found) == 12
    # прочитанные помечены, остальные достроены
    avr = [c for c in layout.cells if c.lead == "aVR"][0]
    assert avr.inferred is False
    v1 = [c for c in layout.cells if c.lead == "V1"][0]
    assert v1.inferred is True


def test_override_accepts_all_formats():
    dets = [TextDetection("V2", 40, 300, 30, 14)]
    for fmt, ncols in [("3x4", 4), ("6x2", 2), ("12x1", 1)]:
        layout = detect_layout(
            "x.png", ocr=FakeOCRBackend(dets), image_size=(1000, 1000),
            layout_override=fmt, use_grid_removal=False,
        )
        assert layout.n_cols == ncols
        assert len(layout.leads_found) == 12
