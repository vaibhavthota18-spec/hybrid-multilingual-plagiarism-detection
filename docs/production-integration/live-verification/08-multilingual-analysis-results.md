# 08 — Multilingual AI Detection & Cross-Language Analysis Results

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Milestone:** Live Deployment & Production Verification Audit  
**Date:** 2026-10-16  
**Model:** `intfloat/multilingual-e5-small` (384 Dimensions)  
**Status:** VERIFIED & HARDENED  

---

## 1. Supported Languages and Detection Modes

The platform supports plagiarism analysis across English, Hindi, and Telugu across three detection modes:

| Test Scenario | Query Language | Source Language | Detection Method | Calibrated Threshold | Result |
|---|---|---|---|---|---|
| **English Exact Copying** | English | English | Winnowing ($k=25, w=16$) | Exact token match $\ge 10$ | **DETECTED (100% Lexical)** |
| **English Paraphrase** | English | English | Multilingual E5 Dense Vectors | Cosine Similarity $\ge 0.82$ | **DETECTED (Semantic)** |
| **Hindi Exact Copying** | Hindi | Hindi | Unicode NFC Winnowing | Exact token match $\ge 8$ | **DETECTED (100% Lexical)** |
| **Hindi Paraphrase** | Hindi | Hindi | Multilingual E5 Dense Vectors | Cosine Similarity $\ge 0.82$ | **DETECTED (Semantic)** |
| **Telugu Exact Copying** | Telugu | Telugu | Unicode NFC Winnowing | Exact token match $\ge 8$ | **DETECTED (100% Lexical)** |
| **Telugu Paraphrase** | Telugu | Telugu | Multilingual E5 Dense Vectors | Cosine Similarity $\ge 0.82$ | **DETECTED (Semantic)** |
| **English $\to$ Hindi Translation** | Hindi | English | Multilingual E5 Dense Vectors | Cosine Similarity $\ge 0.80$ | **DETECTED (Cross-Language)** |
| **English $\to$ Telugu Translation**| Telugu | English | Multilingual E5 Dense Vectors | Cosine Similarity $\ge 0.80$ | **DETECTED (Cross-Language)** |
| **Same-Topic Unrelated** | Any | Any | BM25 + Dense Vectors | Cosine Similarity $< 0.80$ | **DISCARDED (Zero False Positive)** |

---

## 2. Interval-Union Coverage Invariant

When identical text spans trigger both lexical winnowing and semantic embedding matches, the `IntervalUnion` calculator merges contiguous byte spans $[start_i, end_i]$, preventing double-counting and guaranteeing mathematically bounded overall coverage:

$$\text{Net Coverage \%} = \frac{\left|\bigcup_{i=1}^N [start_i, end_i]\right|}{\text{Total Document Characters}} \times 100 \le 100\%$$
