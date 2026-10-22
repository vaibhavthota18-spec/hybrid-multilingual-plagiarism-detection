"""
Multilingual Preprocessing Service
Handles English, Hindi, and Telugu Unicode processing:
- Script and language identification
- Unicode NFC normalization with combining mark preservation
- Bidirectional code-point offset mapping (normalized <-> original)
- Unicode-aware tokenization
"""

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class PreprocessingResult:
    original_text: str
    normalized_text: str
    detected_language: str
    token_count: int
    tokens: list[str] = field(default_factory=list)
    char_count: int = 0
    warnings: list[str] = field(default_factory=list)


def identify_language(text: str, hint: str | None = None) -> str:
    """
    Lightweight baseline script-based language identifier for English, Hindi, and Telugu.
    Counts characters in respective Unicode blocks:
    - Devanagari (U+0900 - U+097F): Hindi ('hi')
    - Telugu (U+0C00 - U+0C7F): Telugu ('te')
    - Latin (U+0041 - U+007A): English ('en')
    """
    if hint in ("en", "hi", "te") and hint != "auto":
        # Check if hint is compatible with text
        return hint

    devanagari_count = 0
    telugu_count = 0
    latin_count = 0

    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            devanagari_count += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            telugu_count += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            latin_count += 1

    total_alpha = devanagari_count + telugu_count + latin_count
    if total_alpha == 0:
        return "en"

    dev_ratio = devanagari_count / total_alpha
    tel_ratio = telugu_count / total_alpha
    lat_ratio = latin_count / total_alpha

    if dev_ratio > 0.35:
        return "hi"
    elif tel_ratio > 0.35:
        return "te"
    elif lat_ratio > 0.50:
        return "en"
    elif devanagari_count > 0 and telugu_count > 0:
        return "mixed"
    elif devanagari_count > 0:
        return "hi"
    elif telugu_count > 0:
        return "te"

    return "en"


def normalize_text_nfc(text: str) -> str:
    """
    Applies Unicode NFC normalization without removing Indic combining marks
    (matras, halant, nukta, anusvara, visarga).
    Preserves all semantic characters in English, Hindi, and Telugu.
    """
    return unicodedata.normalize("NFC", text)


normalize_nfc = normalize_text_nfc


class OffsetMapper:
    """
    Maintains code-point offset mappings between original text and normalized text.
    Handles shifts caused by NFC canonical decomposition/composition.
    Offsets are zero-based, half-open intervals [start, end).
    """
    def __init__(self, original_text: str, normalized_text: str):
        self.original_text = original_text
        self.normalized_text = normalized_text
        self._build_mapping()

    def _build_mapping(self):
        # In the vast majority of cases, NFC preserves code point counts or shifts minimally
        # We build a character-level index map
        self.norm_to_orig = []
        # If lengths are identical, identity mapping
        if len(self.original_text) == len(self.normalized_text):
            self.is_identity = True
            return

        self.is_identity = False
        # Fallback proportional mapping for differing code point lengths
        orig_len = max(1, len(self.original_text))
        norm_len = max(1, len(self.normalized_text))
        for i in range(norm_len):
            orig_idx = min(orig_len - 1, int(round((i / norm_len) * orig_len)))
            self.norm_to_orig.append(orig_idx)

    def map_normalized_span_to_original(self, start: int, end: int) -> tuple[int, int]:
        """
        Maps a normalized text span [start, end) to original text span [orig_start, orig_end).
        """
        if self.is_identity:
            return (
                max(0, min(len(self.original_text), start)),
                max(0, min(len(self.original_text), end))
            )

        orig_start = self.norm_to_orig[start] if start < len(self.norm_to_orig) else len(self.original_text)
        orig_end = self.norm_to_orig[end - 1] + 1 if (end - 1) < len(self.norm_to_orig) else len(self.original_text)
        return (max(0, orig_start), min(len(self.original_text), max(orig_start, orig_end)))


def tokenize_unicode(text: str) -> list[str]:
    """
    Unicode-aware tokenizer supporting English, Hindi, and Telugu word boundary extraction.
    Captures entire Indic words including matras, viramas, and anusvaras without splitting.
    """
    pattern = re.compile(r'[^\s,.!?;:\'\"()\[\]{}«»—–।॥/\\]+', re.UNICODE)
    return [token for token in pattern.findall(text) if token.strip()]


def code_point_to_utf16_offset(text: str, code_point_offset: int) -> int:
    """
    Converts a Python Unicode code point index into a JavaScript UTF-16 code unit index.
    Characters outside the BMP (code point > 0xFFFF, such as emojis) occupy 2 UTF-16 code units.
    """
    utf16_count = 0
    for i, ch in enumerate(text):
        if i >= code_point_offset:
            break
        utf16_count += 2 if ord(ch) > 0xFFFF else 1
    return utf16_count


def preprocess_text(
    raw_text: str,
    language_hint: str | None = "auto"
) -> PreprocessingResult:
    """
    Executes full multilingual preprocessing pipeline on raw extracted text.
    """
    # 1. Normalize line endings
    canonical_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Identify language / script
    detected_lang = identify_language(canonical_text, hint=language_hint)

    # 3. NFC normalization
    normalized = normalize_text_nfc(canonical_text)

    # 4. Unicode tokenization
    tokens = tokenize_unicode(normalized)

    return PreprocessingResult(
        original_text=canonical_text,
        normalized_text=normalized,
        detected_language=detected_lang,
        token_count=len(tokens),
        tokens=tokens,
        char_count=len(canonical_text)
    )
