"""Сопоставление распознанного текста с одним из 12 отведений.

Главная идея надёжности: словарь ЗАКРЫТЫЙ — всего 12 имён. Поэтому даже
если OCR ошибётся в паре символов, мы притянем результат к ближайшему
корректному имени. А посторонний текст (ФИО, "25mm/s", дата) не похож ни на
одно имя и корректно отсеивается.
"""
from __future__ import annotations

from rapidfuzz import fuzz, process

from ecg_layout.leads import CANONICAL_LEADS

# Нормализованный вид ("V1") -> каноническое имя ("V1").
_NORM_TO_CANON: dict[str, str] = {}


def _normalize(text: str) -> str:
    """Приводим текст к единому виду: верхний регистр, только буквы/цифры."""
    return "".join(ch for ch in text.upper() if ch.isalnum())


# Заполняем словарь нормализованных имён + распространённые ошибки OCR.
for _lead in CANONICAL_LEADS:
    _NORM_TO_CANON[_normalize(_lead)] = _lead

# Частые путаницы OCR для V-отведений (буква вместо цифры).
# Важно: НЕ включаем "L"->"1" — заглавная L не похожа на 1 и конфликтует с aVL
# (испорченное "aVL" -> "VL" ошибочно стало бы "V1").
_V_CONFUSIONS = {"I": "1", "O": "0", "S": "5", "B": "8", "Z": "2", "G": "6"}
for _n in range(1, 7):
    for _bad, _good in _V_CONFUSIONS.items():
        if _good == str(_n):
            _NORM_TO_CANON[f"V{_bad}"] = f"V{_n}"

_CANON_KEYS = list(_NORM_TO_CANON.keys())

# Порог похожести (0..100). Ниже — считаем, что это не подпись отведения.
_MATCH_CUTOFF = 82.0

# Паттерн augmented-отведений: aVR / aVL / aVF. На реальных ЭКГ фигурная
# строчная «a» часто читается OCR как o/G/W/α и т.п. Но различающая информация —
# в хвосте: V + R/L/F. Поэтому 3-символьный токен вида "?V[RLF]" уверенно
# относим к нужному отведению (напр. "oVL"->aVL, "GVF"->aVF).
_AUG_SUFFIX = {"VR": "aVR", "VL": "aVL", "VF": "aVF"}


def match_text_to_lead(text: str) -> tuple[str | None, float]:
    """Пытается распознать текст как отведение.

    Возвращает (каноническое_имя, оценка 0..100) или (None, оценка), если
    текст не похож ни на одно отведение.
    """
    norm = _normalize(text)
    if not norm:
        return None, 0.0

    # Точное совпадение (быстрый и самый надёжный путь).
    if norm in _NORM_TO_CANON:
        return _NORM_TO_CANON[norm], 100.0

    # Augmented-отведение по хвосту "V[RLF]" при испорченной первой букве.
    if len(norm) == 3 and norm[1] == "V" and norm[2] in "RLF":
        return _AUG_SUFFIX[norm[1:]], 90.0

    # Иначе — ближайшее по расстоянию редактирования из закрытого словаря.
    best = process.extractOne(norm, _CANON_KEYS, scorer=fuzz.ratio)
    if best is None:
        return None, 0.0
    key, score, _ = best
    if score >= _MATCH_CUTOFF:
        return _NORM_TO_CANON[key], float(score)
    return None, float(score)
