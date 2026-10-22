# Winnowing Algorithm and Fingerprint Generation

## 1. Mathematical Formulation

The Winnowing algorithm (Schleimer, Wilkerson, & Aiken, 2003) is a local document fingerprinting technique designed to detect shared substrings while bounding the density of selected fingerprints.

### Parameter Definitions:
- **$k$-gram length ($k$)**: The number of contiguous tokens comprising an atomic fingerprintable unit ($k = 25$).
- **Window size ($w$)**: The number of adjacent $k$-gram hashes considered in each sliding window ($w = 16$).
- **Guarantee threshold ($t$)**: The minimum match length guaranteed to be detected:
  $$t = k + w - 1 = 25 + 16 - 1 = 40 \text{ tokens}$$
- Any shared passage of length $\ge t$ tokens will reliably produce at least one shared fingerprint.
- No shared passage of length $< k$ tokens will produce a match.

---

## 2. Polynomial Rolling Hash ($O(1)$ Sliding Window)

To compute $k$-gram hashes in $O(N)$ total time rather than $O(N \cdot k)$, we implement a 64-bit polynomial rolling hash over token hashes.

### Individual Token Hash (FNV-1a 64-bit)
Individual string tokens are first mapped to 64-bit unsigned integers using FNV-1a:
$$h_0 = 14695981039346656037$$
$$h_{i+1} = (h_i \oplus \text{byte}_i) \cdot 1099511628211$$

### Polynomial Rolling Formulation
Given a sequence of token hashes $c_1, c_2, \dots, c_k$:
$$H(c_1, \dots, c_k) = \left( \sum_{i=1}^k c_i \cdot B^{k-i} \right) \bmod M$$
where:
- **Base ($B$)**: $313$ (a prime larger than typical 8-bit alphabet sizes)
- **Modulus ($M$)**: $2^{61} - 1 = 2305843009213693951$ (the 9th Mersenne prime)

### $O(1)$ Rolling Transition
When sliding the window by one token (dropping $c_t$ and appending $c_{t+k}$):
$$H_{t+1} = \left( \left( H_t - c_t \cdot B^{k-1} \right) \cdot B + c_{t+k} \right) \bmod M$$

Negative values resulting from subtraction are normalized into the range $[0, M-1]$:
$$H_{t+1} = (H_{t+1} + M) \bmod M$$

This operation requires zero loops and executes in $O(1)$ constant time per token.

---

## 3. Monotonic Deque Sliding Window Minimum

The Winnowing rule selects the minimum hash value within each sliding window of length $w$. When multiple positions share the minimum value, the **rightmost minimum** is selected to maximize the duration before a new fingerprint must be chosen.

Using a naive search would result in $O(N \cdot w)$ complexity. We implement an optimal $O(N)$ algorithm using a **Monotonic Increasing Deque**:

```python
class MonotonicMinDeque:
    def __init__(self):
        self.deque = collections.deque() # stores (hash_value, position)

    def push(self, val: int, pos: int):
        # Evict all elements with value >= val (maintains strictly increasing order)
        # Note: using >= ensures that when values are equal, the newer (rightmost) wins
        while self.deque and self.deque[-1][0] >= val:
            self.deque.pop()
        self.deque.append((val, pos))

    def pop_older_than(self, min_pos: int):
        while self.deque and self.deque[0][1] < min_pos:
            self.deque.popleft()

    def get_min(self) -> tuple[int, int]:
        return self.deque[0]
```

Each $k$-gram hash enters the deque once and leaves the deque at most once, providing guaranteed amortized $O(1)$ time per window slide and $O(N)$ overall complexity for document fingerprinting.

---

## 4. Short Document Fallback

When an uploaded document contains fewer than $k$ tokens ($N < k = 25$):
1. A sliding $k$-gram window cannot be constructed.
2. Rather than silently omitting the document from comparison, the engine activates the **Short Document Fallback**.
3. All available tokens $1 \dots N$ are combined into a single bounded hash with $position = 0$.
4. This ensures short titles, single-sentence abstracts, and brief paragraphs remain indexed and searchable.
