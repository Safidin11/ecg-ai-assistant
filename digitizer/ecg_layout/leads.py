"""Канонический список 12 отведений ЭКГ и порядок для итогового массива."""
from __future__ import annotations

# Канонический порядок отведений (как в PTB-XL и в нашем сигнале [12, N]).
CANONICAL_LEADS: list[str] = [
    "I", "II", "III",
    "aVR", "aVL", "aVF",
    "V1", "V2", "V3", "V4", "V5", "V6",
]

# Индекс отведения в массиве [12, N] по его имени.
LEAD_TO_INDEX: dict[str, int] = {name: i for i, name in enumerate(CANONICAL_LEADS)}
