"""Тесты сопоставления текста с отведениями (закрытый словарь)."""
from ecg_layout.matching import match_text_to_lead


def test_exact_matches():
    for text in ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V6"]:
        lead, score = match_text_to_lead(text)
        assert lead == text
        assert score == 100.0


def test_case_and_spaces_insensitive():
    assert match_text_to_lead("avr")[0] == "aVR"
    assert match_text_to_lead(" V 1 ")[0] == "V1"
    assert match_text_to_lead("AVF")[0] == "aVF"


def test_ocr_digit_confusion_in_v_leads():
    # OCR часто путает 1<->I, 5<->S и т.п. в V-отведениях
    assert match_text_to_lead("VI")[0] == "V1"
    assert match_text_to_lead("VS")[0] == "V5"


def test_garbage_is_rejected():
    for junk in ["25mm/s", "10mm/mV", "Ivanov", "2026-07-18", "HR 75"]:
        lead, _ = match_text_to_lead(junk)
        assert lead is None
