# VS Code Direct Jump Commands for Professor Demonstration

These commands can be run directly in Windows Terminal, PowerShell, or Command Prompt to instantly open Visual Studio Code navigated directly to the exact file and line number of each core algorithm.

**Project Root Directory:**
```powershell
cd "C:\Users\vaibh\OneDrive\Documents\plagarism engine"
```

---

## 1. Top 10 Core Algorithm Opening Commands

### 1. Schleimer Winnowing Algorithm ($k=25, w=16$)
Opens the monotonic deque sliding-window minimum fingerprinting logic:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\lexical\winnowing.py:106"
```

### 2. Polynomial Rolling Hash ($O(1)$ Sliding Window)
Opens the rolling hash subtraction and addition step using Mersenne prime modulus:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\lexical\rolling_hash.py:65"
```

### 3. Okapi BM25 Index & Retrieval Scoring
Opens the Robertson-Spärck Jones IDF and BM25 term weighting functions:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\lexical\bm25.py:57"
```

### 4. Non-Overlapping Interval Union Coverage
Opens the interval union algorithm that prevents double-counting overlapping match spans:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\lexical\coverage.py:22"
```

### 5. Multilingual E5 Embedding Model Provider
Opens the SentenceTransformer model loader, L2 normalization, and query/passage prefixing:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\semantic\provider.py:128"
```

### 6. Vector Cosine Similarity Search (Matrix Dot Product)
Opens the vectorized NumPy dot-product cosine similarity computation:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\storage\vector_store.py:240"
```

### 7. Semantic Paraphrase & Cross-Language Classification
Opens the threshold evaluation that classifies findings into paraphrase vs cross-language:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\semantic\matcher.py:188"
```

### 8. Hybrid Lexical + Semantic Evidence Fusion
Opens the multi-source interval deduplication and weighted scoring formula:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\hybrid_service.py:288"
```

### 9. Human Reviewer Dynamic Re-Scoring Invariant
Opens the real-time re-scoring logic that updates coverage when findings are excluded or cited:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\hybrid_service.py:475"
```

### 10. Dual PDF Report Generation Engine
Opens the headless Chromium print-to-pdf pipeline and ReportLab fallback generator:
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\reports\report_generator.py:691"
```

---

## 2. Additional Essential Modules

### Passage Alignment (Seed-and-Extend)
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\lexical\aligner.py:78"
```

### Indic Language Identification (Script Unicode Block Counter)
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\backend\src\plagiarism\services\preprocessing.py:27"
```

### Frontend Analysis Initiation & Polling Loop
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\web\src\pages\WorkflowPage.tsx:221"
```

### Frontend Side-by-Side Results & Audit Interface
```powershell
code -g "C:\Users\vaibh\OneDrive\Documents\plagarism engine\apps\web\src\pages\ResultsDashboardPage.tsx:65"
```
