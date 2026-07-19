"""Детекция строк ЭКГ по сигналу (горизонтальные полосы отведений).

Идея (из статьи Wu et al.): каждое отведение занимает горизонтальную полосу,
между полосами — пустое место. Считаем «чернильный профиль» по строкам
(сколько тёмных пикселей в каждой строке картинки), находим полосы сигнала
и пустые промежутки между ними. Число полос = число строк раскладки.

Это надёжнее, чем считать строки по подписям: работает, даже если подписи
не читаются.
"""
from __future__ import annotations

import numpy as np


def _row_ink_profile(ink_mask: np.ndarray) -> np.ndarray:
    """Доля чернил в каждой строке картинки (0..1)."""
    return ink_mask.mean(axis=1)


def _smooth(profile: np.ndarray, win: int) -> np.ndarray:
    """Скользящее среднее, чтобы убрать мелкий шум профиля."""
    if win <= 1:
        return profile
    kernel = np.ones(win) / win
    return np.convolve(profile, kernel, mode="same")


def detect_row_bands(
    ink_mask: np.ndarray,
    active_frac: float = 0.06,
    min_band_frac: float = 0.02,
    min_gap_frac: float = 0.01,
) -> list[tuple[int, int]]:
    """Находит вертикальные полосы отведений.

    ink_mask — булева маска чернил (True = сигнал/подпись).
    active_frac — строка «активна», если чернил больше этой доли от пика.
    min_band_frac — полосы тоньше этой доли высоты отбрасываем (шум).
    min_gap_frac — промежутки уже этой доли высоты игнорируем (сливаем полосы).

    Возвращает список (y_top, y_bottom) для каждой полосы, сверху вниз.
    """
    h = ink_mask.shape[0]
    profile = _row_ink_profile(ink_mask)
    profile = _smooth(profile, max(1, int(0.004 * h)))

    peak = float(profile.max())
    if peak <= 0:
        return []
    thresh = peak * active_frac
    active = profile > thresh

    # находим непрерывные участки активных строк
    raw_bands: list[tuple[int, int]] = []
    y = 0
    while y < h:
        if active[y]:
            y0 = y
            while y < h and active[y]:
                y += 1
            raw_bands.append((y0, y - 1))
        else:
            y += 1

    if not raw_bands:
        return []

    # сливаем полосы, разделённые слишком маленьким промежутком
    min_gap = min_gap_frac * h
    merged: list[list[int]] = [list(raw_bands[0])]
    for y0, y1 in raw_bands[1:]:
        if y0 - merged[-1][1] <= min_gap:
            merged[-1][1] = y1
        else:
            merged.append([y0, y1])

    # отбрасываем слишком тонкие полосы (шум)
    min_band = min_band_frac * h
    bands = [(y0, y1) for y0, y1 in merged if (y1 - y0) >= min_band]
    return bands


def detect_n_rows(ink_mask: np.ndarray, **kwargs) -> int:
    """Число строк раскладки = число полос сигнала."""
    return len(detect_row_bands(ink_mask, **kwargs))


# Число строк -> стандартный формат. С запасом на погрешность детекции
# (плоские отведения теряются, соседние с высокими зубцами сливаются).
def standard_format_from_rows(n_rows: int) -> dict:
    """По числу полос сигнала возвращает наиболее вероятный формат раскладки.

    Возвращает {'template': имя, 'n_cols': колонок, 'n_rows_detected': n_rows}.
    """
    if n_rows <= 4:
        template, n_cols = "standard_3x4", 4
    elif n_rows <= 8:
        template, n_cols = "standard_6x2", 2
    else:
        template, n_cols = "standard_12x1", 1
    return {"template": template, "n_cols": n_cols, "n_rows_detected": n_rows}
