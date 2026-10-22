# Repository Audit & Initial State Assessment

> **Phase:** Phase 0 — Requirements Analysis & Complete Blueprint  
> **Target Project Root:** `C:\Users\vaibh\OneDrive\Documents\plagarism engine`  
> **Audit Date:** October 2026  
> **Status:** Completed

---

## 1. Project Directory Verification

The project root was resolved and verified against the user-supplied path:
- **Canonical Resolved Path:** `C:\Users\vaibh\OneDrive\Documents\plagarism engine`
- **Filesystem Existence:** Confirmed (`Test-Path` returned `True`).
- **Access & Permissions:** Confirmed. Probe file write/delete test succeeded with code `0`.
- **Nesting Check:** Confirmed single-level root. No duplicate nested folder (such as `plagiarism-platform/plagiarism-platform/`) exists.

---

## 2. Initial Directory State

An initial audit of the workspace directory was performed prior to Phase 0 execution:
- **Initial File Count:** 0 files (directory was completely empty).
- **Hidden Files / Dotfiles:** None detected.
- **Git Repository:** Not yet initialized. No `.git/` folder present.
- **Existing Application Code:** None present. No legacy frontend or backend code was overwritten or deleted.

---

## 3. Review of Legacy Algorithms & Scope Deprecation

In earlier conceptual drafts of the plagiarism platform (and general academic text-comparison assignments), four classical algorithms were frequently cited:
1. **Naive String Search (`O(N * M)`):** Brute-force substring matching.
2. **Knuth-Morris-Pratt (KMP) (`O(N + M)`):** Prefix-function linear search for exact patterns.
3. **Rabin-Karp (`O(N + M)` average):** Rolling-hash substring matching.
4. **Suffix Tree (`O(N)` construction, `O(M)` query):** Suffix indexing for substring queries.

### Architectural Audit & Decommissioning Decision
As documented in the Master Project Specification Version 3.0 and ratified in this Phase 0 architecture:
- **Naive Algorithm:** **EXCLUDED** from the production pipeline. Inefficient for multi-page documents and corpus-scale retrieval (`O(N*M)` complexity leads to severe latency degradation).
- **Knuth-Morris-Pratt (KMP):** **EXCLUDED** from the primary candidate retrieval pipeline. KMP requires a single pre-known pattern string; it does not solve multi-pattern inverted indexing, cross-document corpus matching, or paraphrasing.
- **Rabin-Karp Rolling Hash:** **RETAINED IN ESSENCE & UPGRADED TO WINNOWING.** The core rolling-hash concept (polynomial rolling hash) is preserved and formalized as **Winnowing** (Schleimer et al., 2003). Winnowing selects local minimum hash fingerprints within sliding windows, providing guaranteed bounds on match detection while reducing storage requirements by 90–95%.
- **Suffix Tree:** **EXCLUDED FROM INITIAL PIPELINE.** Suffix trees incur severe memory overhead (typically 10–20 bytes per character) and do not support fuzzy paraphrased or cross-lingual matching. Local sequence alignment (Smith-Waterman token-level alignment) is chosen instead for bounded passage verification.

### Scope Rationalization Summary
| Historical Algorithm | Architectural Assessment | Phase 0 Decision | Production Replacement |
|---|---|---|---|
| Naive String Search | Brute-force, unacceptable time complexity | **Excluded** | Winnowing Fingerprinting & BM25 |
| Knuth-Morris-Pratt | Single-pattern only, no corpus indexing | **Excluded** | Inverted Fingerprint Index |
| Rabin-Karp | Effective rolling hash concept | **Adapted** | Winnowing Rolling Hash Fingerprinting |
| Suffix Tree | High memory overhead, brittle to edits | **Excluded** | Token-Level Local Alignment |

---

## 4. Phase Roadmap Alignment

The project roadmap has been aligned to Version 4.0:
- **Phase 0:** Requirements Analysis, System Architecture, and Complete Project Blueprint *(Current)*
- **Phase 1:** Engineering Foundation (Docker, Backend/Frontend skeletons, PostgreSQL + pgvector, Redis, CI)
- **Phase 2:** Document Ingestion, Unicode Normalization, and Corpus Management
- **Phase 3:** Lexical Detection Pipeline (Winnowing, BM25, Local Alignment)
- **Phase 4:** Semantic and Hybrid Detection (Multilingual E5 Embeddings, pgvector, Candidate Fusion)
- **Phase 5:** Multilingual Evaluation & Benchmarking (English, Hindi, Telugu)
- **Phase 6:** Product UX, Explainability, Citation Exclusions, and PDF Reporting
- **Phase 7:** Production Hardening, Security, Observability, and Final Deployment

---

## 5. Audit Conclusion

The workspace is clean, verified, and free of architectural contradictions or legacy codebase clutter. Phase 0 artifacts will be authored directly into this verified directory structure without altering external files.
