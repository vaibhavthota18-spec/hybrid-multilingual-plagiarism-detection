"""
Unit Tests for Multilingual Preprocessing Service
Verifies English, Hindi, and Telugu script identification, NFC normalization,
combining mark preservation, and code-point offset mappings.
"""

from plagiarism.services.preprocessing import (
    OffsetMapper,
    code_point_to_utf16_offset,
    identify_language,
    normalize_text_nfc,
    preprocess_text,
    tokenize_unicode,
)


def test_identify_language_english():
    text = "The quick brown fox jumps over the lazy dog. Academic plagiarism detection."
    assert identify_language(text) == "en"


def test_identify_language_hindi():
    text = "साहित्यिक चोरी का पता लगाने के लिए बहुभाषी प्रणाली का विकास और परीक्षण किया जा रहा है।"
    assert identify_language(text) == "hi"


def test_identify_language_telugu():
    text = "బహుభాషా సాహిత్య చౌర్యం గుర్తించే పరిశోధనా వ్యవస్థను సమర్థవంతంగా అభివృద్ధి చేస్తున్నాము."
    assert identify_language(text) == "te"


def test_identify_language_with_hint():
    text = "Ambiguous text with short characters"
    assert identify_language(text, hint="hi") == "hi"


def test_unicode_nfc_normalization():
    # Combining character sequence e + acute accent (U+0065 U+0301) vs composed é (U+00E9)
    decomposed = "e\u0301cole"
    composed = "\u00e9cole"
    assert normalize_text_nfc(decomposed) == composed


def test_hindi_combining_marks_preserved():
    # Hindi word 'हिंदी' (ha + i-matra + anusvara + da + ii-matra)
    hindi_word = "हिंदी"
    normalized = normalize_text_nfc(hindi_word)
    # Check virama / matras are not stripped
    assert "ि" in normalized
    assert "ं" in normalized
    assert "ी" in normalized
    assert len(normalized) == len(hindi_word)


def test_telugu_combining_marks_preserved():
    # Telugu word 'విశ్వవిద్యాలయం' (University)
    telugu_word = "విశ్వవిద్యాలయం"
    normalized = normalize_text_nfc(telugu_word)
    # Check virama (polu U+0C4D) and vowel signs preserved
    assert "\u0C4D" in normalized  # Telugu virama
    assert len(normalized) == len(telugu_word)


def test_offset_mapper_identity():
    text = "Machine learning and artificial intelligence."
    mapper = OffsetMapper(text, text)
    orig_start, orig_end = mapper.map_normalized_span_to_original(8, 16)
    assert orig_start == 8
    assert orig_end == 16
    assert text[orig_start:orig_end] == "learning"


def test_tokenize_unicode_multilingual():
    text = "English words, हिंदी शब्द, మరియు తెలుగు పదాలు!"
    tokens = tokenize_unicode(text)
    assert "English" in tokens
    assert "words" in tokens
    assert "हिंदी" in tokens
    assert "शब्द" in tokens
    assert "మరియు" in tokens
    assert "తెలుగు" in tokens
    assert "పదాలు" in tokens


def test_code_point_to_utf16_offset():
    # Regular ASCII string: 1 code point == 1 UTF-16 code unit
    ascii_str = "hello"
    assert code_point_to_utf16_offset(ascii_str, 3) == 3

    # String containing supplementary plane character (e.g. emoji U+1F600 Grinning Face)
    # Emoji is 1 code point in Python, but 2 code units in UTF-16
    emoji_str = "Hi 😀 world"
    # Index 3 is '😀' (1 code point). At index 5 ('w'), code units should be 3 + 2 + 1 = 6
    assert code_point_to_utf16_offset(emoji_str, 5) == 6


def test_full_preprocessing_pipeline():
    hindi_text = "साहित्यिक चोरी का पता लगाने के लिए बहुभाषी प्रणाली।"
    result = preprocess_text(hindi_text)
    assert result.detected_language == "hi"
    assert result.token_count > 5
    assert result.char_count == len(hindi_text)
    assert result.original_text == hindi_text
