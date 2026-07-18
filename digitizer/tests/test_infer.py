"""Тесты инференса раскладки — на синтетических координатах подписей.

Реальная картинка не нужна: подставляем позиции подписей руками и проверяем,
что раскладка (строки/колонки, отведения, временные отрезки, ритм) выводится
правильно для 3x4, 6x2 и 12x1.
"""
from ecg_layout.infer import infer_layout
from ecg_layout.types import LeadLabel


def _label(lead: str, cx: float, cy: float) -> LeadLabel:
    return LeadLabel(lead=lead, cx=cx, cy=cy, bbox=(cx - 10, cy - 6, 20, 12))


def _cell_by_lead(layout, lead):
    matches = [c for c in layout.cells if c.lead == lead]
    return matches


def test_layout_3x4_with_rhythm():
    W, H = 1200, 1000
    rows_y = {0: 200, 1: 500, 2: 800}
    cols_x = {0: 100, 1: 400, 2: 700, 3: 1000}
    grid = [
        ["I", "aVR", "V1", "V4"],
        ["II", "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
    ]
    labels = []
    for r, leads in enumerate(grid):
        for c, lead in enumerate(leads):
            labels.append(_label(lead, cols_x[c], rows_y[r]))
    # ритм-полоса (полное отведение II снизу, слева)
    labels.append(_label("II", 100, 940))

    layout = infer_layout(labels, W, H)

    assert layout.n_cols == 4
    # 3 строки сетки + строка ритма
    assert layout.n_rows == 4

    # V4 стоит в колонке 3 -> начинается с 7.5 с, длится 2.5 с
    v4 = _cell_by_lead(layout, "V4")[0]
    assert v4.col == 3
    assert abs(v4.time_offset_s - 7.5) < 1e-6
    assert abs(v4.duration_s - 2.5) < 1e-6
    assert v4.is_rhythm is False

    # I стоит в колонке 0 -> с 0 с
    i_cell = [c for c in _cell_by_lead(layout, "I") if not c.is_rhythm][0]
    assert i_cell.col == 0
    assert abs(i_cell.time_offset_s) < 1e-6

    # у II есть и клетка сетки, и ритм-полоса
    ii_cells = _cell_by_lead(layout, "II")
    assert any(c.is_rhythm for c in ii_cells)
    rhythm = [c for c in ii_cells if c.is_rhythm][0]
    assert abs(rhythm.duration_s - 10.0) < 1e-6
    assert abs(rhythm.time_offset_s) < 1e-6


def test_layout_6x2():
    W, H = 1000, 1200
    rows_y = [100, 300, 500, 700, 900, 1100]
    left = ["I", "II", "III", "aVR", "aVL", "aVF"]
    right = ["V1", "V2", "V3", "V4", "V5", "V6"]
    labels = []
    for r in range(6):
        labels.append(_label(left[r], 100, rows_y[r]))
        labels.append(_label(right[r], 600, rows_y[r]))

    layout = infer_layout(labels, W, H)

    assert layout.n_cols == 2
    assert layout.n_rows == 6
    # 2 колонки -> каждая по 5 секунд
    v1 = _cell_by_lead(layout, "V1")[0]
    assert v1.col == 1
    assert abs(v1.time_offset_s - 5.0) < 1e-6
    assert abs(v1.duration_s - 5.0) < 1e-6
    # ритм-полос в чистой 6x2 нет
    assert all(c.is_rhythm is False for c in layout.cells)


def test_layout_12x1():
    W, H = 800, 1300
    leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    labels = [_label(lead, 100, 50 + i * 100) for i, lead in enumerate(leads)]

    layout = infer_layout(labels, W, H)

    assert layout.n_cols == 1
    assert layout.n_rows == 12
    # 1 колонка -> каждое отведение это полные 10 секунд
    for c in layout.cells:
        assert abs(c.time_offset_s) < 1e-6
        assert abs(c.duration_s - 10.0) < 1e-6
        # при 1 колонке ритм-полосу не выделяем
        assert c.is_rhythm is False
