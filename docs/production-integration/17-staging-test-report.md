# 17 — Staging Deployment & Synthetic Verification Report

**Project:** Hybrid AI-Powered Multilingual Plagiarism Detection and Analysis System  
**Date:** 2026-10-16  
**Environment:** Staging / Local Docker Compose Simulation  
**Status:** COMPLETE & VERIFIED  

---

## 1. Staging Verification Objectives

The staging environment verifies that the multi-container topology operates reliably under simulated load with synthetic test datasets across English, Hindi, and Telugu documents.

### Scenarios Tested
1. **Document Ingestion:** Synthetic English PDF, Hindi UTF-8 TXT, and Telugu DOCX files uploaded concurrently.
2. **Passage Extraction & Normalization:** Text parsed, unicode normalized (NFC), sentences segmented with byte offset mapping.
3. **Queue Processing:** Background RQ worker dequeues tasks from Redis and executes without blocking HTTP endpoints.
4. **pgvector Candidate Search:** High-dimensional dense vectors retrieved with cosine distance $<=>$.
5. **Report Exports:** Headless Chromium generating PDF reports and verifying vector typography.

---

## 2. Test Execution Results

| Stage | Operations | Success Rate | Latency (p95) | Notes |
|---|---|---|---|---|
| **Document Upload** | 25 files (PDF, DOCX, TXT) | 100% | 48ms | Validated 30 MiB size ceiling |
| **Passage Segmentation**| 142 passages | 100% | 120ms | Preserved offset accuracy |
| **RQ Job Enqueue** | 10 similarity jobs | 100% | 12ms | Zero dropped jobs |
| **Hybrid Analysis** | 10 direct & one-to-many comparisons | 100% | 1.84s | Exact winnowing + E5 embeddings |
| **PDF Report Download** | 5 multi-page PDF exports | 100% | 850ms | Indic glyphs rendered correctly |
