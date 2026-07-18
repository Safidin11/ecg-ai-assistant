"""Тесты устойчивости распознавания раскладки к реальным дефектам OCR.

Каждый тест воспроизводит конкретное слабое место и проверяет, что оно
закрыто. Реальные картинки не нужны — подставляем координаты подписей.
"""
from ecg_layout.infer import infer_layout
from ecg_layout.matching import match_text_to_lead
from ecg_layout.types import LeadLabel


def _label(lead: str, cx: float, cy: float, w: float = 20, h: float = 12) -> LeadLabel:
    return LeadLabel(lead=lead, cx=cx, cy=cy, bbox=(cx - w / 2, cy - h / 2, w, h), conf=0.9)


def _grid_labels(drop: set[str] | None = None):
    """3x4-раскладка; можно выбросить часть подписей (имитируя пропуск OCR)."""
    drop = drop or set()
    rows_y = [200, 500, 800]
    cols_x = [100, 400, 700, 1000]
    grid = [
        ["I", "aVR", "V1", "V4"],
        ["II", "aVL", "V2", "V5"],
        ["III", "aVF", "V3", "V6"],
    ]
    labels = []
    for r, leads in enumerate(grid):
        for c, lead in enumerate(leads):
            if lead not in drop:
                labels.append(_label(lead, cols_x[c], rows_y[r]))
    return labels


def test_missing_label_does_not_shift_time():
    # Роняем aVL (середина 2-й строки). Соседи V2/V5 НЕ должны сдвинуться.
    layout = infer_layout(_grid_labels(drop={"aVL"}), 1200, 1000)
    v2 = [c for c in layout.cells if c.lead == "V2"][0]
    v5 = [c for c in layout.cells if c.lead == "V5"][0]
    # V2 в колонке 2 -> 5..7.5 с; V5 в колонке 3 -> 7.5..10 с
    assert v2.col == 2 and abs(v2.time_offset_s - 5.0) < 1e-6
    assert v5.col == 3 and abs(v5.time_offset_s - 7.5) < 1e-6
    # раскладка всё ещё 4 колонки
    assert layout.n_cols == 4


def test_duplicate_detection_is_deduped():
    labels = _grid_labels()
    # дубль V1 рядом с оригиналом (как будто OCR вернул две рамки)
    labels.append(_label("V1", 705, 205))
    layout = infer_layout(labels, 1200, 1000)
    v1_cells = [c for c in layout.cells if c.lead == "V1" and not c.is_rhythm]
    assert len(v1_cells) == 1
    assert layout.n_cols == 4  # дубль не создал лишнюю колонку


def test_row_jitter_does_not_split_rows():
    # добавляем вертикальный разброс подписям внутри строк
    labels = _grid_labels()
    for i, lb in enumerate(labels):
        lb.cy += (i % 3 - 1) * 4  # ±4 пикселя
        lb.bbox = (lb.bbox[0], lb.cy - 6, lb.bbox[2], lb.bbox[3])
    layout = infer_layout(labels, 1200, 1000)
    assert layout.n_rows == 3
    assert layout.n_cols == 4


def test_partial_top_row_is_not_rhythm():
    # Верхняя строка с пропуском НЕ должна становиться ритм-полосой.
    layout = infer_layout(_grid_labels(drop={"aVR", "V1", "V4"}), 1200, 1000)
    # I остаётся обычной клеткой сетки, не ритмом
    i_cell = [c for c in layout.cells if c.lead == "I"][0]
    assert i_cell.is_rhythm is False


def test_bottom_sparse_row_is_rhythm():
    labels = _grid_labels()
    labels.append(_label("II", 100, 950))  # полноширинная ритм-полоса снизу
    layout = infer_layout(labels, 1200, 1000)
    rhythm = [c for c in layout.cells if c.is_rhythm]
    assert len(rhythm) == 1
    assert rhythm[0].lead == "II"
    assert abs(rhythm[0].duration_s - 10.0) < 1e-6


def test_coverage_metric():
    full = infer_layout(_grid_labels(), 1200, 1000)
    assert abs(full.coverage - 1.0) < 1e-6
    partial = infer_layout(_grid_labels(drop={"V5", "V6"}), 1200, 1000)
    assert abs(partial.coverage - 10 / 12) < 1e-6


def test_matching_no_longer_confuses_avl_with_v1():
    # испорченное "aVL" -> "VL" не должно ошибочно стать V1
    lead, _ = match_text_to_lead("VL")
    assert lead != "V1"


def test_missing_left_column_still_4_cols():
    # OCR не прочитал весь левый столбец (I, II, III). Раскладка должна
    # остаться 4-колоночной, а aVR — попасть в колонку 1 (t=2.5..5), не 0.
    labels = _grid_labels(drop={"I", "II", "III"})
    layout = infer_layout(labels, 1200, 1000)
    assert layout.n_cols == 4
    avr = [c for c in layout.cells if c.lead == "aVR"][0]
    assert avr.col == 1
    assert abs(avr.time_offset_s - 2.5) < 1e-6
    v4 = [c for c in layout.cells if c.lead == "V4"][0]
    assert v4.col == 3
    assert abs(v4.time_offset_s - 7.5) < 1e-6


def test_matching_recovers_augmented_leads_with_broken_a():
    # реальные ошибки OCR на фигурной строчной "a" (см. img11.jpg)
    assert match_text_to_lead("oVL")[0] == "aVL"
    assert match_text_to_lead("GVF")[0] == "aVF"
    assert match_text_to_lead("oVR")[0] == "aVR"
    assert match_text_to_lead("0VF")[0] == "aVF"
