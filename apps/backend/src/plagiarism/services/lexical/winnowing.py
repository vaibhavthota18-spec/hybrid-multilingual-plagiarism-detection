"""
Winnowing Algorithm Implementation (Schleimer, Wilkerson, Aiken 2003).
Generates compact, representative document fingerprints with formal guarantee:
Any shared verbatim token sequence of length >= t = k + w - 1 is guaranteed to share >= 1 fingerprint.
"""

from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Tuple

from plagiarism.services.lexical.tokenizer import LexicalToken
from plagiarism.services.lexical.rolling_hash import RollingHash, fnv1a_64


@dataclass(frozen=True)
class Fingerprint:
    hash_val: int              # 64-bit integer hash of selected k-gram
    token_start: int           # 0-indexed starting token index of k-gram
    token_end: int             # 0-indexed ending token index of k-gram (exclusive)
    char_start: int            # 0-indexed Unicode code-point start in raw text
    char_end: int              # 0-indexed Unicode code-point end in raw text
    is_short_fallback: bool = False  # Flag for documents smaller than k tokens


class WinnowingEngine:
    """
    Computes Winnowing fingerprints from token sequences.
    Default parameters:
      k = 25 tokens (k-gram size)
      w = 16 hashes (window size)
      Guarantee: t = k + w - 1 = 40 tokens
    """

    def __init__(self, k: int = 25, w: int = 16, algorithm_version: str = "winnowing-k25-w16-v1"):
        self.k = k
        self.w = w
        self.algorithm_version = algorithm_version
        self.t = k + w - 1

    def fingerprint_tokens(self, tokens: List[LexicalToken]) -> List[Fingerprint]:
        """
        Runs Winnowing across an ordered list of LexicalTokens.
        Returns a deduplicated list of selected Fingerprint records with exact original text offsets.
        """
        n = len(tokens)
        if n == 0:
            return []

        # Short text fallback: when total tokens is less than k
        if n < self.k:
            if n < 3:
                # Fewer than 3 tokens: cannot reliably fingerprint
                return []
            # Generate a single short fallback fingerprint covering all available tokens
            token_hashes = [fnv1a_64(t.norm_text) for t in tokens]
            rh = RollingHash(token_hashes, k=n)
            kgrams = rh.compute_all()
            if not kgrams:
                return []
            start_idx, h_val = kgrams[0]
            return [
                Fingerprint(
                    hash_val=h_val,
                    token_start=0,
                    token_end=n,
                    char_start=tokens[0].start_char,
                    char_end=tokens[-1].end_char,
                    is_short_fallback=True,
                )
            ]

        # 1. Compute 64-bit FNV-1a hash for each token
        token_hashes = [fnv1a_64(t.norm_text) for t in tokens]

        # 2. Compute sliding k-gram polynomial hashes
        rh = RollingHash(token_hashes, k=self.k)
        kgrams: List[Tuple[int, int]] = rh.compute_all()
        num_kgrams = len(kgrams)

        if num_kgrams == 0:
            return []

        # If total k-grams is less than window w, select global rightmost minimum
        if num_kgrams < self.w:
            min_idx = 0
            min_hash = kgrams[0][1]
            for i in range(1, num_kgrams):
                # Prefer rightmost minimum on tie
                if kgrams[i][1] <= min_hash:
                    min_hash = kgrams[i][1]
                    min_idx = i

            token_start = kgrams[min_idx][0]
            token_end = token_start + self.k
            return [
                Fingerprint(
                    hash_val=min_hash,
                    token_start=token_start,
                    token_end=token_end,
                    char_start=tokens[token_start].start_char,
                    char_end=tokens[token_end - 1].end_char,
                    is_short_fallback=False,
                )
            ]

        # 3. Standard Winnowing over sliding windows of size w
        # Uses monotonic deque for O(N) sliding-window minimum with rightmost tie-breaking
        selected_fingerprints: List[Fingerprint] = []
        last_recorded_pos: Optional[int] = None

        # Each element in deque is (kgram_index, hash_value)
        # We maintain elements in strictly increasing order of hash_value.
        # For rightmost tie-breaking: if new hash <= existing hash at tail, pop tail!
        deq: deque = deque()

        for i in range(num_kgrams):
            curr_pos, curr_hash = kgrams[i]

            # Remove elements that have fallen outside the current window [i - w + 1, i]
            while deq and deq[0][0] <= i - self.w:
                deq.popleft()

            # Maintain monotonic order: pop elements with greater OR EQUAL hash
            # Popping on equal ensures the rightmost minimum remains at the tail / becomes chosen
            while deq and deq[-1][1] >= curr_hash:
                deq.pop()

            deq.append((i, curr_hash))

            # Once the window reaches size w (starting at index w - 1)
            if i >= self.w - 1:
                min_kgram_idx, min_val = deq[0]

                # Record fingerprint if the selected minimum position changed
                if last_recorded_pos != min_kgram_idx:
                    t_start = kgrams[min_kgram_idx][0]
                    t_end = t_start + self.k
                    c_start = tokens[t_start].start_char
                    c_end = tokens[t_end - 1].end_char

                    selected_fingerprints.append(
                        Fingerprint(
                            hash_val=min_val,
                            token_start=t_start,
                            token_end=t_end,
                            char_start=c_start,
                            char_end=c_end,
                            is_short_fallback=False,
                        )
                    )
                    last_recorded_pos = min_kgram_idx

        return selected_fingerprints
