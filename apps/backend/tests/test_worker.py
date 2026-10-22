"""
Unit Tests for Background Worker Tasks and Queue Lifecycle
"""

import pytest
from plagiarism.jobs.tasks import ping_job, simulate_calculation, failing_job


def test_ping_job_execution():
    """Verify ping_job executes deterministically and returns expected structure."""
    result = ping_job(echo="health_probe_payload")
    assert result["status"] == "pong"
    assert result["echo"] == "health_probe_payload"
    assert "timestamp" in result
    assert "worker_pid" in result


def test_simulate_calculation_operations():
    """Verify simulate_calculation produces exact arithmetic results."""
    add_res = simulate_calculation(12, 18, "add")
    assert add_res["result"] == 30

    mult_res = simulate_calculation(6, 7, "multiply")
    assert mult_res["result"] == 42

    sub_res = simulate_calculation(100, 45, "subtract")
    assert sub_res["result"] == 55

    div_res = simulate_calculation(50, 5, "divide")
    assert div_res["result"] == 10.0


def test_simulate_calculation_division_by_zero():
    """Verify simulate_calculation raises ValueError when dividing by zero."""
    with pytest.raises(ValueError, match="Division by zero"):
        simulate_calculation(10, 0, "divide")


def test_simulate_calculation_unknown_operation():
    """Verify simulate_calculation raises ValueError for unsupported operations."""
    with pytest.raises(ValueError, match="Unsupported operation"):
        simulate_calculation(10, 5, "modulus")


def test_failing_job_error_propagation():
    """Verify failing_job intentionally raises RuntimeError for failure retry testing."""
    with pytest.raises(RuntimeError, match="Controlled test failure probe"):
        failing_job("Controlled test failure probe")
