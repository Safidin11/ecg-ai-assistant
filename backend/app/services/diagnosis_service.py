"""Сервис модели диагностики: сигнал -> вероятности диагнозов.

ВНИМАНИЕ: это ЗАГЛУШКА (stub). Она не запускает нейросеть, а выдаёт
случайные (но правдоподобные) вероятности по 5 обобщённым классам PTB-XL.
На этапе 1 сюда подключим предобученную на PTB-XL модель, на этапе 3 —
свою. Внешний интерфейс (функция predict и класс PredictResult) при этом
менять не придётся.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Обобщённые (superclass) диагнозы PTB-XL
DIAGNOSIS_CLASSES = {
    "NORM": "Норма",
    "MI": "Инфаркт миокарда",
    "STTC": "Изменения ST/T",
    "CD": "Нарушение проводимости",
    "HYP": "Гипертрофия",
}

# Версия "модели" — попадёт в БД в поле model_version.
# У настоящей модели здесь будет что-то вроде "ptbxl-resnet1d-v1".
MODEL_VERSION = "stub-0.1"


@dataclass
class PredictResult:
    """Результат предсказания для одного сигнала."""

    model_version: str
    probabilities: dict[str, float]   # {код класса: вероятность}
    diagnosis: str                    # код наиболее вероятного класса


def predict(signal: np.ndarray) -> PredictResult:
    """ЗАГЛУШКА: возвращает случайные вероятности по классам PTB-XL.

    Аргумент signal сейчас используется только чтобы "посеять" генератор
    случайных чисел (для стабильности ответа на один и тот же сигнал).
    Реальная модель будет прогонять сигнал через нейросеть.
    """
    # seed из суммы сигнала — один и тот же сигнал даёт один и тот же ответ
    seed = int(abs(np.nan_to_num(signal).sum()) * 1000) % (2**32)
    rng = np.random.default_rng(seed)

    codes = list(DIAGNOSIS_CLASSES.keys())
    raw = rng.random(len(codes))
    probs = raw / raw.sum()  # нормируем, чтобы сумма была 1

    probabilities = {code: round(float(p), 4) for code, p in zip(codes, probs)}
    top_code = max(probabilities, key=probabilities.get)

    return PredictResult(
        model_version=MODEL_VERSION,
        probabilities=probabilities,
        diagnosis=top_code,
    )
