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

Ключевая устойчивость: колонка отведения определяется по ГЛОБАЛЬНОЙ модели
колонок (кластеризация X по всем подписям), а не по порядку внутри строки.
Поэтому если OCR пропустил одну подпись, соседние НЕ сдвигаются по времени.
"""
from __future__ import annotations

import statistics

from ecg_layout.types import LayoutMap, LeadCell, LeadLabel


def cluster_1d(values: list[float], tol: float) -> list[int]:
    """Разбивает числа на группы: новая группа начинается, когда разрыв > tol.

    Возвращает для каждого исходного значения номер его группы (0 — наименьшие).
    Группировка идёт относительно центра текущей группы, а не последнего
    значения — так группа не «уползает» при плавном дрейфе координат.
    """
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    clusters = [0] * len(values)
    cid = 0
    cluster_sum = float(values[order[0]])
    cluster_n = 0
    for k, idx in enumerate(order):
        v = values[idx]
        if cluster_n > 0 and (v - cluster_sum / cluster_n) > tol:
            cid += 1
            cluster_sum = 0.0
            cluster_n = 0
        clusters[idx] = cid
        cluster_sum += v
        cluster_n += 1
    return clusters


def _label_scale(labels: list[LeadLabel]) -> tuple[float, float]:
    """Типичные ширина и высота подписи — база для адаптивных допусков."""
    widths = [lb.bbox[2] for lb in labels if lb.bbox[2] > 0]
    heights = [lb.bbox[3] for lb in labels if lb.bbox[3] > 0]
    med_w = statistics.median(widths) if widths else 0.0
    med_h = statistics.median(heights) if heights else 0.0
    return med_w, med_h


def _dedup_labels(labels: list[LeadLabel], dedup_tol: float) -> list[LeadLabel]:
    """Убирает повторные детекции одного и того же отведения рядом.

    OCR иногда возвращает две перекрывающиеся рамки на одну подпись — из-за
    этого можно ошибиться в числе колонок. Оставляем более уверенную.
    """
    kept: list[LeadLabel] = []
    for lb in sorted(labels, key=lambda x: x.conf, reverse=True):
        dup = False
        for k in kept:
            if k.lead == lb.lead:
                if abs(k.cx - lb.cx) <= dedup_tol and abs(k.cy - lb.cy) <= dedup_tol:
                    dup = True
                    break
        if not dup:
            kept.append(lb)
    return kept


def infer_layout(
    labels: list[LeadLabel],
    image_w: float,
    image_h: float,
    total_seconds: float = 10.0,
    row_tol_frac: float = 0.02,
) -> LayoutMap:
    """Строит карту раскладки по подписям.

    image_w/image_h — размеры картинки (используются как нижняя граница
    допусков). total_seconds — полная длительность записи (обычно 10 с).
    """
    if not labels:
        return LayoutMap(n_rows=0, n_cols=0, total_seconds=total_seconds)

    med_w, med_h = _label_scale(labels)

    # 0. Дедуп повторных детекций одного отведения.
    dedup_tol = max(med_w, med_h, 1.0)
    labels = _dedup_labels(labels, dedup_tol)

    # 1. Строки по Y. Допуск берём от РАЗМЕРА подписи (устойчивее, чем доля
    #    высоты картинки), но не меньше небольшого порога от высоты.
    row_tol = max(2.0 * med_h, row_tol_frac * image_h, 1.0)
    row_ids = cluster_1d([lb.cy for lb in labels], tol=row_tol)
    n_rows = max(row_ids) + 1

    # 2. Колонки по X — ГЛОБАЛЬНО по всем подписям (а не внутри строки).
    col_tol = max(2.0 * med_w, 0.02 * image_w, 1.0)
    col_ids = cluster_1d([lb.cx for lb in labels], tol=col_tol)
    n_cols_main = max(col_ids) + 1

    # раскладываем подписи по строкам
    rows: list[list[tuple[LeadLabel, int]]] = [[] for _ in range(n_rows)]
    for lb, rid, cid in zip(labels, row_ids, col_ids):
        rows[rid].append((lb, cid))
    for row in rows:
        row.sort(key=lambda pair: pair[0].cx)

    # 3. Какие строки «полные» (число подписей == числу колонок) — это сетка.
    full_row_ids = [r for r, row in enumerate(rows) if len(row) == n_cols_main]
    max_full = max(full_row_ids) if full_row_ids else -1
    rhythm_threshold = max(1, n_cols_main // 3)

    seg = total_seconds / n_cols_main  # длительность одной колонки, сек

    cells: list[LeadCell] = []
    for r_idx, row in enumerate(rows):
        # Ритм-полоса: только если есть колонки (>=2), строка разрежена И
        # находится НИЖЕ всей основной сетки. Разреженная строка вверху/в
        # середине — это не ритм, а строка с пропущенной подписью.
        is_rhythm_row = (
            n_cols_main >= 2
            and len(full_row_ids) > 0
            and r_idx > max_full
            and len(row) <= rhythm_threshold
        )
        for lb, cid in row:
            if is_rhythm_row:
                time_offset = 0.0
                duration = total_seconds
                col = 0
            else:
                col = cid  # колонка из глобальной модели — пропуск не сдвигает
                time_offset = col * seg
                duration = seg
            cells.append(
                LeadCell(
                    lead=lb.lead,
                    row=r_idx,
                    col=col,
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
