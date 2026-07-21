"""Канонический порядок 12 отведений (общий для всех форматов)."""
from __future__ import annotations

CANONICAL_LEADS: list[str] = [
    "I", "II", "III",
    "aVR", "aVL", "aVF",
    "V1", "V2", "V3", "V4", "V5", "V6",
]

LEAD_TO_INDEX: dict[str, int] = {name: i for i, name in enumerate(CANONICAL_LEADS)}
