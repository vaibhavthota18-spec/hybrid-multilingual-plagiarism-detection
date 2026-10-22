# Experiment Reproducibility Guide

## 1. Reproducibility Principles

In accordance with scientific benchmarking standards, any researcher or developer running the Phase 5 evaluation scripts must obtain identical outputs without external dependencies or cloud calls.

---

## 2. Deterministic Seeds & Offline Assets

1. **Fixed Model Checkpoint**: `intfloat/multilingual-e5-small` loaded strictly from offline local cache `storage/model_cache/models--intfloat--multilingual-e5-small`.
2. **Fixed Random Seed**: `np.random.RandomState(42)` pinned for all bootstrap resampling experiments.
3. **Deterministic Tokenizer**: Deterministic Karp-Rabin polynomial hash ($B=31, M=2^{32}-1$) with zero randomized salting.

---

## 3. Step-by-Step Reproduction Instructions

From the project root: `C:\Users\vaibh\OneDrive\Documents\plagarism engine`

### Step 1: Validate Dataset Integrity & Leakage
```powershell
apps\backend\.venv\Scripts\python.exe scripts\build_benchmark_dataset.py
```
*Expected Output*: `Successfully loaded and validated 40 examples across ['en', 'hi', 'te'].`

### Step 2: Execute Master Scientific Evaluation
```powershell
apps\backend\.venv\Scripts\python.exe scripts\run_phase5_evaluation.py
```
*Expected Output*:
- Completes calibration in ~5s.
- Evaluates held-out split in ~6s.
- Writes `data/evaluation/evaluation_results.json`.
- Writes `data/evaluation/error_analysis.json`.
- Writes `data/evaluation/calibration_report.json`.

### Step 3: Run Performance Benchmarking
```powershell
apps\backend\.venv\Scripts\python.exe scripts\benchmark_phase5_performance.py
```
*Expected Output*: Saves `data/evaluation/performance_benchmark_results.json`.

### Step 4: Execute Full Pytest Test Suite
```powershell
apps\backend\.venv\Scripts\python.exe -m pytest apps/backend/tests
```
*Expected Output*: `102 passed in ~105s`.

### Step 5: Run Full End-to-End Acceptance Verification
```powershell
apps\backend\.venv\Scripts\python.exe scripts\verify_phase5_e2e.py
```
*Expected Output*: `PHASE 5 ACCEPTANCE RESULT: ALL 14 SCENARIOS PASSED (100%)`.
