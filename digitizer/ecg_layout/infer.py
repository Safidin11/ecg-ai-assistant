"""Вывод раскладки ЭКГ из позиций распознанных подписей.

Вход: список подписей отведений (каждая знает своё имя и координаты центра).
Выход: LayoutMap — сетка строк/колонок, где для каждой клетки известно
отведение, номер строки/колонки и временной отрезок записи.

Как это работает (главная мысль всего блока):
- колонки на картинке = отрезки ВРЕМЕНИ. Если колонок 4, вся запись (10 с)
  делится на 4 куска по 2.5 с; колонка 0 = 0–2.5 с, колонка 1 = 2.5–5 с и т.д.
- строки = группы отведений.
- нижняя полоса на всю ширину (обычно 1 отведение) = ритм-полоса, у неё
  полные 10 с.
"""
from __future__ import annotations

from ecg_layout.types import LayoutMap, LeadCell, LeadLabel


def cluster_1d(values: list[float], tol: float) -> list[int]:
    """Разбивает числа на группы: новая группа начинается, когда разрыв > tol.

    Возвращает для каждого исходного значения номер его группы (0 — наименьшие).
    Используется, чтобы сгруппировать подписи в строки по координате Y.
    """
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    clusters = [0] * len(values)
    cid = 0
    prev = values[order[0]]
    for k, idx in enumerate(order):
        v = values[idx]
        if k > 0 and (v - prev) > tol:
            cid += 1
        clusters[idx] = cid
        prev = v
    return clusters


def infer_layout(
    labels: list[LeadLabel],
    image_w: float,
    image_h: float,
    total_seconds: float = 10.0,
    row_tol_frac: float = 0.035,
) -> LayoutMap:
    """Строит карту раскладки по подписям.

    image_w/image_h — размеры картинки (нужны для масштаба допусков).
    total_seconds — полная длительность записи (обычно 10 с).
    row_tol_frac — какой разброс по вертикали считать "одной строкой"
                   (доля от высоты картинки).
    """
    if not labels:
        return LayoutMap(n_rows=0, n_cols=0, total_seconds=total_seconds)

    # 1. Группируем подписи в строки по Y.
    row_tol = row_tol_frac * image_h
    row_ids = cluster_1d([lb.cy for lb in labels], tol=row_tol)
    n_rows = max(row_ids) + 1

    # для каждой строки — её подписи, отсортированные слева направо
    rows: list[list[LeadLabel]] = [[] for _ in range(n_rows)]
    for lb, rid in zip(labels, row_ids):
        rows[rid].append(lb)
    for row in rows:
        row.sort(key=lambda lb: lb.cx)

    # 2. Число колонок основной сетки = максимальная длина строки.
    row_sizes = [len(r) for r in rows]
    n_cols_main = max(row_sizes)

    # порог: строку считаем ритм-полосой, если в ней подписей заметно меньше,
    # чем в основной сетке (обычно 1). Для 12x1 (n_cols_main=1) ритма нет.
    rhythm_size_threshold = max(1, n_cols_main // 3)

    seg = total_seconds / n_cols_main  # длительность одной колонки, сек

    cells: list[LeadCell] = []
    for r_idx, row in enumerate(rows):
        is_rhythm_row = n_cols_main >= 2 and len(row) <= rhythm_size_threshold
        for c_idx, lb in enumerate(row):
            if is_rhythm_row:
                time_offset = 0.0
                duration = total_seconds
            else:
                time_offset = c_idx * seg
                duration = seg
            cells.append(
                LeadCell(
                    lead=lb.lead,
                    row=r_idx,
                    col=c_idx,
                    bbox=lb.bbox,
                    time_offset_s=time_offset,
                    duration_s=duration,
                    is_rhythm=is_rhythm_row,
                    conf=lb.conf,
                )
            )

    return LayoutMap(
        n_rows=n_rows,
        n_cols=n_cols_main,
        total_seconds=total_seconds,
        cells=cells,
    )
