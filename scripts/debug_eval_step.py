import time
import sys
from pathlib import Path

print("Step 1: Importing modules...", flush=True)
t0 = time.time()
from plagiarism.evaluation.dataset_loader import load_benchmark_dataset, validate_split_leakage
from plagiarism.evaluation.runner import EvaluationRunner
from plagiarism.evaluation.schemas import SplitPartition
print(f"Step 1 Done in {time.time() - t0:.2f}s", flush=True)

print("Step 2: Loading dataset...", flush=True)
t0 = time.time()
dataset = load_benchmark_dataset(Path("data/evaluation/benchmark_dataset_v1.json"))
print(f"Step 2 Done in {time.time() - t0:.2f}s", flush=True)

print("Step 3: Initializing EvaluationRunner...", flush=True)
t0 = time.time()
runner = EvaluationRunner()
print(f"Step 3 Done in {time.time() - t0:.2f}s", flush=True)

calib_examples = [e for e in dataset.examples if e.split == SplitPartition.CALIBRATION]
held_examples = [e for e in dataset.examples if e.split == SplitPartition.HELD_OUT_EVALUATION]

print("Step 4: Calibrating thresholds...", flush=True)
t0 = time.time()
lex_th = runner.calibrate_thresholds(calib_examples, mode="lexical")
print(f"  Calib Lex done in {time.time() - t0:.2f}s: {lex_th}", flush=True)

t0 = time.time()
sem_th = runner.calibrate_thresholds(calib_examples, mode="semantic")
print(f"  Calib Sem done in {time.time() - t0:.2f}s: {sem_th}", flush=True)

t0 = time.time()
hyb_th = runner.calibrate_thresholds(calib_examples, mode="hybrid")
print(f"  Calib Hyb done in {time.time() - t0:.2f}s: {hyb_th}", flush=True)

print("Step 5: Evaluating Held-Out Lexical...", flush=True)
t0 = time.time()
rep_held_lex = runner.run_evaluation(dataset, mode="lexical", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=lex_th)
print(f"  Held Lex done in {time.time() - t0:.2f}s, F1: {rep_held_lex.classification.f1:.2%}", flush=True)

print("Step 6: Evaluating Held-Out Semantic...", flush=True)
t0 = time.time()
rep_held_sem = runner.run_evaluation(dataset, mode="semantic", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=sem_th)
print(f"  Held Sem done in {time.time() - t0:.2f}s, F1: {rep_held_sem.classification.f1:.2%}", flush=True)

print("Step 7: Evaluating Held-Out Hybrid...", flush=True)
t0 = time.time()
rep_held_hyb = runner.run_evaluation(dataset, mode="hybrid", split=SplitPartition.HELD_OUT_EVALUATION, thresholds=hyb_th)
print(f"  Held Hyb done in {time.time() - t0:.2f}s, F1: {rep_held_hyb.classification.f1:.2%}", flush=True)

print("Step 8: Retrieval benchmarks...", flush=True)
t0 = time.time()
ret_lex = runner.run_retrieval_benchmark(held_examples, mode="lexical")
print(f"  Ret Lex done in {time.time() - t0:.2f}s", flush=True)
t0 = time.time()
ret_sem = runner.run_retrieval_benchmark(held_examples, mode="semantic")
print(f"  Ret Sem done in {time.time() - t0:.2f}s", flush=True)
t0 = time.time()
ret_hyb = runner.run_retrieval_benchmark(held_examples, mode="hybrid")
print(f"  Ret Hyb done in {time.time() - t0:.2f}s", flush=True)

print("ALL STEPS COMPLETED SUCCESSFULLY!", flush=True)
