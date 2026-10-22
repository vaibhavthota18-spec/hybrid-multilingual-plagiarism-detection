"""
Lexical Tokenizer with Exact Code-Point and UTF-16 Offset Preservation
Handles English, Hindi (Devanagari matras & danda), Telugu (Brahmic viramas), and mixed texts.
"""

import re
import unicodedata
from dataclasses import dataclass

# Token pattern that does not split Indic combining marks (matras, viramas)
TOKEN_REGEX = re.compile(r'[^\s,.!?;:\'\"()\[\]{}«»—–।॥/\\`~@#$%^&*+=<>|]+', re.UNICODE)


@dataclass(frozen=True)
class LexicalToken:
    text: str              # Original token text as extracted from source
    norm_text: str         # Normalized token for comparison (NFC, case-folded for Latin)
    index: int             # 0-indexed token position in document sequence
    start_char: int        # 0-indexed Unicode code-point start in original text
    end_char: int          # 0-indexed Unicode code-point end in original text
    start_utf16: int       # 0-indexed UTF-16 code unit start for JavaScript DOM
    end_utf16: int         # 0-indexed UTF-16 code unit end for JavaScript DOM
    script: str            # Script identifier: 'LATIN', 'DEVANAGARI', 'TELUGU', 'COMMON'


def build_utf16_offset_map(text: str) -> list[int]:
    """
    Builds a lookup table mapping each Unicode character code-point index to its
    corresponding UTF-16 code unit offset. For characters in the BMP (code point <= 0xFFFF),
    1 code point = 1 code unit. For surrogate pairs (astral characters/emojis), 1 code point = 2 code units.
    Table length is len(text) + 1.
    """
    offsets = [0] * (len(text) + 1)
    acc = 0
    for i, ch in enumerate(text):
        offsets[i] = acc
        acc += 2 if ord(ch) > 0xFFFF else 1
    offsets[len(text)] = acc
    return offsets


def detect_token_script(token_text: str) -> str:
    """Classifies token into primary script based on Unicode block distribution."""
    devanagari_count = 0
    telugu_count = 0
    latin_count = 0
    for ch in token_text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            devanagari_count += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            telugu_count += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A) or (0x00C0 <= cp <= 0x024F):
            latin_count += 1

    if devanagari_count > 0:
        return "DEVANAGARI"
    if telugu_count > 0:
        return "TELUGU"
    if latin_count > 0:
        return "LATIN"
    return "COMMON"


class LexicalTokenizer:
    """
    Deterministic tokenizer producing tokens with exact code-point and UTF-16 coordinates.
    """

    def tokenize(self, raw_text: str) -> list[LexicalToken]:
        """
        Tokenizes raw input text while maintaining strict offset invariant:
        raw_text[token.start_char : token.end_char] == token.text
        """
        if not raw_text:
            return []

        utf16_map = build_utf16_offset_map(raw_text)
        tokens: list[LexicalToken] = []

        token_idx = 0
        for match in TOKEN_REGEX.finditer(raw_text):
            original_token = match.group(0)
            start_char = match.start()
            end_char = match.end()

            # Normalization: Unicode NFC composition
            nfc_token = unicodedata.normalize("NFC", original_token)
            script = detect_token_script(nfc_token)

            # Case folding: lower-case Latin tokens, preserve Brahmic scripts
            if script == "LATIN":
                norm_text = nfc_token.lower()
            else:
                norm_text = nfc_token

            start_utf16 = utf16_map[start_char]
            end_utf16 = utf16_map[end_char]

            tokens.append(
                LexicalToken(
                    text=original_token,
                    norm_text=norm_text,
                    index=token_idx,
                    start_char=start_char,
                    end_char=end_char,
                    start_utf16=start_utf16,
                    end_utf16=end_utf16,
                    script=script,
                )
            )
            token_idx += 1

        return tokens
