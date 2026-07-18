"""Сервис дигитайзера: изображение ЭКГ -> цифровой сигнал.

ВНИМАНИЕ: это ЗАГЛУШКА (stub). Она не читает картинку по-настоящему, а
генерирует синтетический сигнал 12 отведений, чтобы весь пайплайн работал
end-to-end. На этапе 1 сюда подключим готовый сторонний дигитайзер, на
этапе 2 — доработаем свой. Внешний интерфейс (функция digitize и класс
DigitizeResult) при этом менять не придётся.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Стандартные 12 отведений ЭКГ (порядок как в PTB-XL)
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Параметры синтетического сигнала
SAMPLING_RATE = 500          # Гц
DURATION_SECONDS = 10.0      # длительность записи
HEART_RATE_BPM = 75          # "пульс" для фейкового сигнала


@dataclass
class DigitizeResult:
    """Результат оцифровки одного изображения ЭКГ."""

    signal: np.ndarray        # массив формы [12, N] в милливольтах
    sampling_rate: int        # частота дискретизации, Гц
    duration: float           # длительность, сек
    quality_score: float      # оценка качества оцифровки 0..1


def _fake_ecg_beat(n_samples: int, sampling_rate: int) -> np.ndarray:
    """Строит один канал понарошку-ЭКГ: периодические R-пики + лёгкий шум.

    Это НЕ настоящая ЭКГ — просто узнаваемая форма, чтобы было что рисовать
    и сохранять. Заменяется реальным дигитайзером.
    """
    t = np.arange(n_samples) / sampling_rate
    beat_period = 60.0 / HEART_RATE_BPM               # секунд на удар
    phase = (t % beat_period) / beat_period           # 0..1 внутри удара
    # узкий "R-пик" примерно в середине каждого удара
    r_peak = np.exp(-((phase - 0.5) ** 2) / (2 * 0.002))
    noise = 0.02 * np.random.default_rng().standard_normal(n_samples)
    return (1.0 * r_peak + noise).astype(np.float32)


def digitize(image_path: str) -> DigitizeResult:
    """ЗАГЛУШКА: возвращает синтетический сигнал [12, N] в мВ.

    Аргумент image_path сейчас не используется (реальный дигитайзер будет
    читать картинку по этому пути).
    """
    n_samples = int(SAMPLING_RATE * DURATION_SECONDS)
    leads = [_fake_ecg_beat(n_samples, SAMPLING_RATE) for _ in LEAD_NAMES]
    signal = np.vstack(leads)  # форма [12, N]

    return DigitizeResult(
        signal=signal,
        sampling_rate=SAMPLING_RATE,
        duration=DURATION_SECONDS,
        quality_score=0.5,  # заглушка: среднее качество
    )
