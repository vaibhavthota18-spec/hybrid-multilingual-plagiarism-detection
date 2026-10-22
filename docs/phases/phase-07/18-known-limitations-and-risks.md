# Phase 7 — Known Scientific & Implementation Limitations

## 1. Scientific & NLP Limitations
1. **Short Text Sensitivity:**
   - The theoretical Winnowing guarantee applies to matches of length $\ge t = 40$ tokens. Short phrases ($< 15$ tokens) may fall beneath the fingerprint window threshold.
2. **Semantic Similarity vs. Misconduct:**
   - High cosine similarity ($\ge 0.82$) indicates conceptual semantic overlap, not necessarily unethical behavior. Human academic review remains essential.
3. **Cross-Language Translation Quality:**
   - Multilingual E5 captures cross-lingual semantics well for European and major Indic languages, but subtle nuances, poetic metaphors, and colloquialisms may register lower similarity.
4. **Scanned Image PDFs:**
   - The system ingests digital PDFs containing extractable text streams (`pypdf`). Scanned documents containing only raster images without embedded OCR text are outside current scope.

## 2. Localhost Runtime Limitations
1. **Threadpool Concurrency:**
   - Local background processing runs via a 2-worker `ThreadPoolExecutor`. Under heavy multi-user concurrent loads, tasks queue up sequentially.
2. **SQLite Write Concurrency:**
   - While WAL mode enables concurrent reads, SQLite serializes write transactions with a 30-second busy timeout.
3. **CPU Inference Latency:**
   - Dense vector generation runs on CPU. For documents over 100 pages, initial embedding generation may take several seconds.
