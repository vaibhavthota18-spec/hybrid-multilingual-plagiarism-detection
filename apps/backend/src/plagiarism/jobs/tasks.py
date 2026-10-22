"""
Deterministic background worker tasks for infrastructure verification
Phase 1 Scope: Testing worker queue execution without plagiarism analysis algorithms
"""

import hashlib
import os
import time
from datetime import UTC, datetime
from typing import Any


def ping_job(message: str = "ping", echo: str | None = None) -> dict[str, Any]:
    """
    Deterministic probe task to verify Redis queue enqueue, worker dequeue, and execution.
    Returns payload echo, pid, timestamp, and sha256 checksum.
    """
    payload_text = echo if echo is not None else message
    start_time = time.time()
    checksum = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()

    return {
        "status": "pong",
        "echo": payload_text,
        "input_message": payload_text,
        "checksum": checksum,
        "timestamp": datetime.now(UTC).isoformat(),
        "executed_at": datetime.now(UTC).isoformat(),
        "worker_pid": os.getpid(),
        "duration_seconds": round(time.time() - start_time, 6)
    }


def simulate_calculation(a: float, b: float, operation: str = "add") -> dict[str, Any]:
    """
    Deterministic calculation task validating worker math operations and error handling.
    """
    op = operation.lower()
    if op == "add":
        result = a + b
    elif op == "subtract":
        result = a - b
    elif op == "multiply":
        result = a * b
    elif op == "divide":
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    return {"result": result, "a": a, "b": b, "operation": op}


def failing_job(message: str = "Controlled test failure probe") -> None:
    """Deterministic failure task to verify worker exception handling."""
    raise RuntimeError(message)


def process_document_job(
    document_id: str,
    storage_path: str,
    extension: str,
    language_hint: str | None = "auto"
) -> dict[str, Any]:
    """
    Production background worker task for document extraction and passage segmentation.
    Executes in unprivileged worker process reading shared persistent storage.
    """
    from plagiarism.services.executor import get_executor
    executor = get_executor()
    executor.process_document_sync(
        document_id=document_id,
        storage_path=storage_path,
        extension=extension,
        language_hint=language_hint
    )
    return {
        "status": "completed",
        "document_id": document_id,
        "completed_at": datetime.now(UTC).isoformat()
    }


def run_hybrid_analysis_job(
    analysis_id: str,
    owner_user_id: str,
    submission_document_id: str,
    mode: str,
    detection_mode: str = "hybrid",
    reference_document_id: str | None = None,
    reference_document_ids: list[str] | None = None,
    collection_id: str | None = None,
) -> dict[str, Any]:
    """
    Production background worker task for lexical, semantic, and hybrid similarity analysis.
    Executes Winnowing k-gram hashing, BM25 retrieval, and dense E5 embedding cosine comparisons.
    """
    from plagiarism.services.hybrid_service import get_hybrid_service
    service = get_hybrid_service()
    service.run_analysis(
        analysis_id=analysis_id,
        owner_user_id=owner_user_id,
        submission_document_id=submission_document_id,
        mode=mode,
        detection_mode=detection_mode,
        reference_document_id=reference_document_id,
        reference_document_ids=reference_document_ids,
        collection_id=collection_id,
    )
    return {
        "status": "completed",
        "analysis_id": analysis_id,
        "completed_at": datetime.now(UTC).isoformat()
    }

