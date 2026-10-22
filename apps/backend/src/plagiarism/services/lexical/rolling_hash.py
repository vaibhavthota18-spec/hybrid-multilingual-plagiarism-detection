"""
Deterministic 64-Bit FNV-1a Token Hash and Polynomial Rolling Hash over Token K-Grams.
Provides process-independent, mathematically defined hashing without Python's randomized hash().
"""


# 64-bit FNV-1a parameters
FNV_64_PRIME = 0x100000001B3
FNV_64_OFFSET_BASIS = 0xCBF29CE484222325
UINT64_MASK = 0xFFFFFFFFFFFFFFFF

# Polynomial rolling hash parameters (Mersenne prime M61 = 2^61 - 1)
ROLLING_BASE = 313
ROLLING_MODULUS = (1 << 61) - 1


def fnv1a_64(token_str: str) -> int:
    """
    Computes standard 64-bit FNV-1a hash of a token string.
    Completely deterministic across processes and platforms.
    """
    h = FNV_64_OFFSET_BASIS
    for b in token_str.encode("utf-8"):
        h = (h ^ b) * FNV_64_PRIME
        h &= UINT64_MASK
    return h


def compute_kgram_hash(
    token_hashes: list[int],
    base: int = ROLLING_BASE,
    modulus: int = ROLLING_MODULUS
) -> int:
    """
    Computes direct polynomial hash of a list of token hashes:
    H = (sum_{i=0}^{k-1} h_i * base^(k-1-i)) mod modulus
    """
    val = 0
    for h in token_hashes:
        val = (val * base + (h % modulus)) % modulus
    return val


class RollingHash:
    """
    Sliding polynomial rolling hash over a sequence of token hashes.
    Computes k-gram hashes in O(1) time per window step.
    """

    def __init__(
        self,
        token_hashes: list[int],
        k: int,
        base: int = ROLLING_BASE,
        modulus: int = ROLLING_MODULUS
    ):
        self.hashes = token_hashes
        self.k = k
        self.base = base
        self.modulus = modulus
        # Precompute base^(k-1) mod modulus
        self.high_power = pow(base, k - 1, modulus) if k > 0 else 1

    def compute_all(self) -> list[tuple[int, int]]:
        """
        Computes all k-gram hashes for the token sequence.
        Returns a list of tuples: (start_token_index, kgram_hash)
        If len(hashes) < k, returns a single entry with hash of available tokens.
        """
        n = len(self.hashes)
        if n == 0:
            return []

        # Short text fallback: fewer than k tokens
        if n < self.k:
            short_hash = compute_kgram_hash(self.hashes, self.base, self.modulus)
            return [(0, short_hash)]

        results: list[tuple[int, int]] = []

        # Compute initial k-gram hash for window [0 : k]
        current_hash = 0
        for i in range(self.k):
            current_hash = (current_hash * self.base + (self.hashes[i] % self.modulus)) % self.modulus

        results.append((0, current_hash))

        # Slide window across the rest of the tokens
        for i in range(self.k, n):
            old_h = self.hashes[i - self.k] % self.modulus
            new_h = self.hashes[i] % self.modulus

            # Remove outgoing token: (current_hash - old_h * base^(k-1)) mod modulus
            term_to_remove = (old_h * self.high_power) % self.modulus
            current_hash = (current_hash - term_to_remove) % self.modulus
            if current_hash < 0:
                current_hash += self.modulus

            # Shift left and add incoming token
            current_hash = (current_hash * self.base + new_h) % self.modulus
            start_index = i - self.k + 1
            results.append((start_index, current_hash))

        return results
