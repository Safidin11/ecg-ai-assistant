"""Отрисовка чистой цифровой ЭКГ из восстановленного сигнала.

Это НЕ улучшенная фотография — изображение строится заново: стандартная сетка
+ кривые из массива [12, N], в выбранном масштабе (speed мм/с, gain мм/мВ).
Никакого фона, теней и шума исходного фото.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # без экрана, только файл
import matplotlib.pyplot as plt  # noqa: E402

from ecg_layout.leads import LEAD_TO_INDEX  # noqa: E402
from ecg_layout.templates import LAYOUT_TEMPLATES, template_cell_map  # noqa: E402
from pipeline.params import LAYOUT_SPECS, ECGParams  # noqa: E402

_MINOR = "#f4b8bd"   # мелкая клетка 1 мм
_MAJOR = "#e88a92"   # крупная клетка 5 мм
_TRACE = "#111111"   # цвет кривой
_ROW_MM = 24.0       # высота одной строки отведения, мм (диапазон ±1.2 мВ при 10мм/мВ)


def _draw_grid(ax, w_mm: float, h_mm: float) -> None:
    import numpy as np

    for x in np.arange(0, w_mm + 1e-6, 1):
        ax.axvline(x, color=_MINOR, lw=0.4, zorder=0)
    for y in np.arange(0, h_mm + 1e-6, 1):
        ax.axhline(y, color=_MINOR, lw=0.4, zorder=0)
    for x in np.arange(0, w_mm + 1e-6, 5):
        ax.axvline(x, color=_MAJOR, lw=0.8, zorder=1)
    for y in np.arange(0, h_mm + 1e-6, 5):
        ax.axhline(y, color=_MAJOR, lw=0.8, zorder=1)


def render_ecg(signals, params: ECGParams, out_path: str, px_per_mm: int = 6) -> str:
    """Рисует ЭКГ из signals [12, N] и сохраняет в out_path. Возвращает путь."""
    import numpy as np

    spec = LAYOUT_SPECS[params.layout]
    rows, cols = spec["rows"], spec["cols"]
    template = spec["template"]
    cell_map = template_cell_map(template)          # (row,col)->lead
    rhythm = LAYOUT_TEMPLATES[template]["rhythm"]
    n_bands = rows + len(rhythm)

    sr = params.sampling_rate
    col_seconds = params.duration_s / cols
    col_mm = col_seconds * params.speed             # ширина колонки, мм
    w_mm = col_mm * cols
    h_mm = _ROW_MM * n_bands

    fig, ax = plt.subplots(figsize=(w_mm / 25.4, h_mm / 25.4), dpi=px_per_mm * 25.4)
    _draw_grid(ax, w_mm, h_mm)

    def plot_segment(lead, row_idx, x0_mm, t0_s, t1_s):
        if lead not in LEAD_TO_INDEX:
            return
        sig = signals[LEAD_TO_INDEX[lead]]
        i0, i1 = int(round(t0_s * sr)), int(round(t1_s * sr))
        seg = sig[i0:i1]
        if len(seg) == 0:
            return
        t = np.linspace(0, (t1_s - t0_s), len(seg))
        x = x0_mm + t * params.speed                      # мм по горизонтали
        baseline = (row_idx + 0.5) * _ROW_MM              # центр строки (в мм, ось вниз)
        y = baseline - seg * params.gain                  # отклонение вверх = вверх
        ax.plot(x, y, color=_TRACE, lw=0.8, zorder=2)
        ax.text(x0_mm + 1, baseline - _ROW_MM / 2 + 3, lead,
                fontsize=7, color=_TRACE, zorder=3)

    # основная сетка
    for (r, c), lead in cell_map.items():
        plot_segment(lead, r, c * col_mm, c * col_seconds, (c + 1) * col_seconds)
    # ритм-полосы снизу (полная длительность)
    for i, lead in enumerate(rhythm):
        plot_segment(lead, rows + i, 0.0, 0.0, params.duration_s)

    ax.set_xlim(0, w_mm)
    ax.set_ylim(h_mm, 0)          # ось Y вниз (как на бумаге)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=px_per_mm * 25.4, facecolor="white")
    plt.close(fig)
    return out_path
