"""
Phase 6 Tests: Reviewer Workflow, Finding Exclusions, and Multi-Format Report Generation.
Verifies PATCH review decisions, reviewer-adjusted score recomputation, and PDF/HTML/JSON report generation.
"""

import time
import pytest
from fastapi.testclient import TestClient

from plagiarism.main import app
from plagiarism.storage.local_db import get_local_repo


@pytest.fixture
def client():
    return TestClient(app)


def _wait_for_doc(client, doc_id: str, timeout: float = 10.0):
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"/api/v1/documents/{doc_id}")
        if r.status_code == 200 and r.json().get("status") == "completed":
            return
        time.sleep(0.05)


def test_reviewer_workflow_and_score_adjustment(client):
    """
    Verifies that human reviewer decisions (keep, exclude, quoted_cited) update the finding
    and dynamically recompute the reviewer-adjusted union coverage without corrupting
    original detector metrics.
    """
    repo = get_local_repo()

    # Ingest submission and reference documents
    sub_text = (
        "Artificial intelligence and deep learning models have rapidly transformed contemporary research methodologies. "
        "The quick brown fox jumps over the lazy dog repeatedly in various natural language benchmarks. "
        "Natural language processing enables systems to comprehend multilingual syntax with high precision."
    )
    ref_text = (
        "The quick brown fox jumps over the lazy dog repeatedly in various natural language benchmarks. "
        "Natural language processing enables systems to comprehend multilingual syntax with high precision."
    )

    sub_resp = client.post(
        "/api/v1/documents",
        files={"file": ("phase6_sub.txt", sub_text.encode("utf-8"), "text/plain")}
    )
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["document_id"]

    ref_resp = client.post(
        "/api/v1/documents",
        files={"file": ("phase6_ref.txt", ref_text.encode("utf-8"), "text/plain")}
    )
    assert ref_resp.status_code == 201
    ref_id = ref_resp.json()["document_id"]

    _wait_for_doc(client, sub_id)
    _wait_for_doc(client, ref_id)

    # Run synchronous hybrid analysis
    analysis_resp = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": sub_id,
            "mode": "direct",
            "reference_document_id": ref_id,
            "detection_mode": "hybrid",
        }
    )
    assert analysis_resp.status_code == 202
    analysis_id = analysis_resp.json()["analysis_id"]

    # Fetch initial analysis results
    res_resp = client.get(f"/api/v1/analyses/{analysis_id}")
    assert res_resp.status_code == 200
    res = res_resp.json()
    orig_score = res["hybrid_evidence_coverage_percent"]
    assert orig_score > 0.0
    findings = res["findings"]
    assert len(findings) >= 1

    first_finding = findings[0]
    finding_id = first_finding["finding_id"]
    assert first_finding["review_decision"] == "unreviewed"

    # Step 1: Submit 'keep' decision with notes
    rev1_resp = client.patch(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/review",
        json={
            "decision": "keep",
            "notes": "Verified copied verbatim from reference."
        }
    )
    assert rev1_resp.status_code == 200
    rev1 = rev1_resp.json()
    assert rev1["finding"]["review_decision"] == "keep"
    assert rev1["finding"]["reviewer_notes"] == "Verified copied verbatim from reference."
    assert rev1["status_counts"]["keep"] >= 1
    # Original score intact
    assert rev1["original_evidence_coverage_percent"] == orig_score
    assert rev1["reviewer_adjusted_coverage_percent"] > 0.0
    kept_score = rev1["reviewer_adjusted_coverage_percent"]

    # Step 2: Submit 'exclude' decision (finding should now be omitted from coverage)
    rev2_resp = client.patch(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/review",
        json={
            "decision": "exclude",
            "notes": "Common idiom / standard phrasing, excluded from plagiarism tally."
        }
    )
    assert rev2_resp.status_code == 200
    rev2 = rev2_resp.json()
    assert rev2["finding"]["review_decision"] == "exclude"
    assert rev2["finding"]["is_excluded"] is True
    # Reviewer adjusted score must strictly decrease when the finding is excluded
    assert rev2["reviewer_adjusted_coverage_percent"] < kept_score

    # Step 3: Submit 'quoted_cited' decision
    rev3_resp = client.patch(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/review",
        json={
            "decision": "quoted_cited",
            "notes": "Accurately cited in footnotes."
        }
    )
    assert rev3_resp.status_code == 200
    rev3 = rev3_resp.json()
    assert rev3["finding"]["review_decision"] == "quoted_cited"
    assert rev3["finding"]["is_quoted"] is True


def test_report_downloads_all_formats(client):
    """
    Verifies the generation and download of JSON, HTML, and PDF reports.
    """
    # Ingest submission and reference documents
    doc1_resp = client.post(
        "/api/v1/documents",
        files={"file": ("report_sub.txt", b"Machine learning models require robust evaluation metrics across diverse test suites.", "text/plain")}
    )
    assert doc1_resp.status_code == 201
    doc1_id = doc1_resp.json()["document_id"]

    doc2_resp = client.post(
        "/api/v1/documents",
        files={"file": ("report_ref.txt", b"Machine learning models require robust evaluation metrics across diverse test suites.", "text/plain")}
    )
    assert doc2_resp.status_code == 201
    doc2_id = doc2_resp.json()["document_id"]

    _wait_for_doc(client, doc1_id)
    _wait_for_doc(client, doc2_id)

    analysis_resp = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": doc1_id,
            "mode": "direct",
            "reference_document_id": doc2_id,
            "detection_mode": "hybrid",
        }
    )
    assert analysis_resp.status_code == 202
    analysis_id = analysis_resp.json()["analysis_id"]

    # 1. JSON Report
    json_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=json")
    assert json_resp.status_code == 200
    json_data = json_resp.json()
    assert "metrics" in json_data
    assert "findings" in json_data
    assert "disclaimer" in json_data
    assert json_data["analysis_id"] == analysis_id

    # 2. HTML Report (printable, self-contained)
    html_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=html")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    html_content = html_resp.text
    assert "<!DOCTYPE html>" in html_content
    assert "Similarity & Plagiarism Audit Report" in html_content
    assert "report_sub.txt" in html_content

    # 3. PDF Report (formal binary stream)
    pdf_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=pdf")
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["content-type"]
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000
