"""Тесты достройки раскладки по стандартному шаблону."""
from ecg_layout.complete import complete_layout
from ecg_layout.infer import infer_layout
from ecg_layout.types import LeadLabel


def _label(lead: str, cx: float, cy: float) -> LeadLabel:
    return LeadLabel(lead=lead, cx=cx, cy=cy, bbox=(cx - 10, cy - 6, 20, 12), conf=0.9)


def _read_leads_missing_left_column_and_v2():
    """Имитация img11: прочитаны все, кроме левого столбца (I,II,III) и V2."""
    rows_y = [200, 500, 800]
    cols_x = [100, 400, 700, 1000]
    grid = [
        ["I", "aVR", "V1", "V4"],
        ["II", "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
    ]
    missing = {"I", "II", "III", "V2"}
    labels = []
    for r, leads in enumerate(grid):
        for c, lead in enumerate(leads):
            if lead not in missing:
                labels.append(_label(lead, cols_x[c], rows_y[r]))
    return labels


def test_completion_fills_missing_leads():
    layout = infer_layout(_read_leads_missing_left_column_and_v2(), 1200, 1000)
    assert layout.n_cols == 4
    before = set(layout.leads_found)
    assert "I" not in before and "V2" not in before

    layout = complete_layout(layout, 1200, 1000)
    after = set(layout.leads_found)
    # теперь все 12 отведений на месте
    assert {"I", "II", "III", "V2"} <= after
    assert len(after) == 12

    # достроенные помечены inferred, прочитанные — нет
    i_cell = [c for c in layout.cells if c.lead == "I"][0]
    assert i_cell.inferred is True and i_cell.col == 0
    assert abs(i_cell.time_offset_s) < 1e-6
    v2_cell = [c for c in layout.cells if c.lead == "V2"][0]
    assert v2_cell.inferred is True and v2_cell.col == 2
    assert abs(v2_cell.time_offset_s - 5.0) < 1e-6
    avr_cell = [c for c in layout.cells if c.lead == "aVR"][0]
    assert avr_cell.inferred is False

    assert "completed" in layout.source


def test_completion_skips_when_no_template_matches():
    # разрозненные, не образующие стандартную сетку подписи -> не достраиваем
    labels = [_label("V1", 100, 100), _label("V2", 100, 300)]
    layout = infer_layout(labels, 1000, 1000)
    n_before = len(layout.cells)
    layout = complete_layout(layout, 1000, 1000)
    assert len(layout.cells) == n_before  # ничего не добавили
    assert "completed" not in layout.source
