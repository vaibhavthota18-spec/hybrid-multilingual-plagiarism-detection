"""
Phase 3 Backend Integration Tests for Lexical Detection APIs.
Tests /api/v1/analyses endpoints, direct/one-to-many/corpus modes,
multilingual alignment, and coverage calculation on live test client.
"""

import io

import pytest
from fastapi.testclient import TestClient

from plagiarism.main import app
from plagiarism.storage.local_db import get_local_repo


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def repo():
    return get_local_repo()


def test_analysis_direct_mode_exact_copy(client):
    """Uploads a source document and a derivative with an exact copied passage."""
    # 1. Upload source document
    ref_text = (
        "In this foundational paper on computer science, we examine algorithmic efficiency. "
        "The quick brown fox jumps over the lazy dog repeatedly across multiple systems. "
        "Sorting algorithms exhibit distinct lower bounds depending on comparison constraints."
    )
    resp_ref = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("ref.txt", io.BytesIO(ref_text.encode("utf-8")), "text/plain")},
        data={"title": "Computer Science Foundation Paper"}
    )
    assert resp_ref.status_code == 201
    ref_id = resp_ref.json()["document_id"]

    # 2. Upload submission document containing copied passage
    sub_text = (
        "Preliminary introduction by student researcher on software performance. "
        "The quick brown fox jumps over the lazy dog repeatedly across multiple systems. "
        "This conclude the novel investigation performed by the authors."
    )
    resp_sub = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("sub.txt", io.BytesIO(sub_text.encode("utf-8")), "text/plain")},
        data={"title": "Student Term Paper"}
    )
    assert resp_sub.status_code == 201
    sub_id = resp_sub.json()["document_id"]

    # 3. Create and execute Direct Analysis
    resp_analysis = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": sub_id,
            "mode": "direct",
            "reference_document_id": ref_id,
        }
    )
    assert resp_analysis.status_code == 202
    job_status = resp_analysis.json()
    analysis_id = job_status["analysis_id"]
    assert job_status["status"] == "completed"

    # 4. Fetch Analysis Results
    resp_res = client.get(f"/api/v1/analyses/{analysis_id}")
    assert resp_res.status_code == 200
    res = resp_res.json()

    assert res["status"] == "completed"
    assert res["overall_lexical_coverage_percent"] > 20.0
    assert res["overall_lexical_coverage_percent"] < 100.0
    assert len(res["sources"]) == 1
    assert res["sources"][0]["reference_document_id"] == ref_id
    assert len(res["findings"]) >= 1

    # Check offset validity
    f = res["findings"][0]
    assert f["category"] == "exact_copy"
    assert "quick brown fox jumps over the lazy dog" in f["submission_excerpt"]
    assert sub_text[f["submission_start_offset"] : f["submission_end_offset"]] == f["submission_excerpt"]
    assert ref_text[f["reference_start_offset"] : f["reference_end_offset"]] == f["reference_excerpt"]


def test_analysis_unrelated_documents_zero_coverage(client):
    """Compares two completely unrelated documents; verifies 0.0% coverage and zero findings."""
    doc_a = "Quantum mechanics explores wave-particle duality and uncertainty principles in subatomic physics."
    doc_b = "Culinary arts and Italian gastronomy emphasize extra virgin olive oil, basil, and aged balsamic vinegar."

    ra = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("physics.txt", io.BytesIO(doc_a.encode("utf-8")), "text/plain")},
        data={"title": "Physics Paper"}
    ).json()
    rb = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("cooking.txt", io.BytesIO(doc_b.encode("utf-8")), "text/plain")},
        data={"title": "Gastronomy Paper"}
    ).json()

    resp_analysis = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": ra["document_id"],
            "mode": "direct",
            "reference_document_id": rb["document_id"],
        }
    )
    assert resp_analysis.status_code == 202
    analysis_id = resp_analysis.json()["analysis_id"]

    res = client.get(f"/api/v1/analyses/{analysis_id}").json()
    assert res["status"] == "completed"
    assert res["overall_lexical_coverage_percent"] == 0.0
    assert len(res["findings"]) == 0
    assert len(res["sources"]) == 0


def test_analysis_one_to_many_and_corpus_mode(client):
    """Tests One-to-Many and Corpus mode comparison workflows."""
    # Shared passage
    shared = "Statistical regression models evaluate independent variables to predict dependent outcomes."

    ref1_text = f"First reference text. {shared} Additional econometrics data."
    ref2_text = "Second reference text talking about completely unrelated marine biology and coral reefs."
    sub_text = f"Student thesis submission. {shared} Concluding remarks on the experiment."

    r1 = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("ref1.txt", io.BytesIO(ref1_text.encode("utf-8")), "text/plain")},
        data={"title": "Econometrics Source"}
    ).json()
    r2 = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("ref2.txt", io.BytesIO(ref2_text.encode("utf-8")), "text/plain")},
        data={"title": "Biology Source"}
    ).json()
    sub = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("sub_thesis.txt", io.BytesIO(sub_text.encode("utf-8")), "text/plain")},
        data={"title": "Student Thesis"}
    ).json()

    # 1. One-to-many test
    resp_o2m = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": sub["document_id"],
            "mode": "one_to_many",
            "reference_document_ids": [r1["document_id"], r2["document_id"]],
        }
    )
    assert resp_o2m.status_code == 202
    res_o2m = client.get(f"/api/v1/analyses/{resp_o2m.json()['analysis_id']}").json()
    assert res_o2m["status"] == "completed"
    assert res_o2m["overall_lexical_coverage_percent"] > 0.0
    # Only ref1 matched; ref2 had zero match
    matched_ref_ids = [s["reference_document_id"] for s in res_o2m["sources"]]
    assert r1["document_id"] in matched_ref_ids
    assert r2["document_id"] not in matched_ref_ids

    # 2. Corpus mode test
    col_resp = client.post(
        "/api/v1/collections",
        json={"name": "Academic Evaluation Corpus", "description": "Benchmark texts"}
    ).json()
    col_id = col_resp["collection_id"]

    client.post(f"/api/v1/collections/{col_id}/documents", json={"document_id": r1["document_id"]})
    client.post(f"/api/v1/collections/{col_id}/documents", json={"document_id": r2["document_id"]})

    resp_corpus = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": sub["document_id"],
            "mode": "corpus",
            "collection_id": col_id,
        }
    )
    assert resp_corpus.status_code == 202
    res_corpus = client.get(f"/api/v1/analyses/{resp_corpus.json()['analysis_id']}").json()
    assert res_corpus["status"] == "completed"
    assert res_corpus["overall_lexical_coverage_percent"] > 0.0


def test_analysis_multilingual_hindi_and_telugu(client):
    """Tests exact match detection on Hindi Devanagari and Telugu Brahmic texts."""
    hi_shared = "साहित्यिक चोरी शैक्षणिक अखंडता और अनुसंधान के मानकों का उल्लंघन करती है।"
    te_shared = "సాహిత్య చౌర్యం విద్యా సమగ్రత మరియు పరిశోధన ప్రమాణాలను ఉల్లంఘిస్తుంది."

    hi_ref = f"हिंदी संदर्भ स्रोत। {hi_shared} शोध के नियम।"
    hi_sub = f"शोधार्थी का आलेख। {hi_shared} निष्कर्ष।"

    te_ref = f"తెలుగు మూల గ్రంథం. {te_shared} ముగింపు."
    te_sub = f"విద్యార్థి వ్యాసం. {te_shared} అధ్యయనం."

    r_hi = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("hi_ref.txt", io.BytesIO(hi_ref.encode("utf-8")), "text/plain")},
        data={"title": "Hindi Reference"}
    ).json()
    s_hi = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("hi_sub.txt", io.BytesIO(hi_sub.encode("utf-8")), "text/plain")},
        data={"title": "Hindi Submission"}
    ).json()

    res_hi = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={"submission_document_id": s_hi["document_id"], "mode": "direct", "reference_document_id": r_hi["document_id"]}
    ).json()
    analysis_hi = client.get(f"/api/v1/analyses/{res_hi['analysis_id']}").json()

    assert analysis_hi["status"] == "completed"
    assert analysis_hi["overall_lexical_coverage_percent"] > 30.0
    assert len(analysis_hi["findings"]) >= 1
    assert "साहित्यिक चोरी" in analysis_hi["findings"][0]["submission_excerpt"]

    # Telugu test
    r_te = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("te_ref.txt", io.BytesIO(te_ref.encode("utf-8")), "text/plain")},
        data={"title": "Telugu Reference"}
    ).json()
    s_te = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("te_sub.txt", io.BytesIO(te_sub.encode("utf-8")), "text/plain")},
        data={"title": "Telugu Submission"}
    ).json()

    res_te = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={"submission_document_id": s_te["document_id"], "mode": "direct", "reference_document_id": r_te["document_id"]}
    ).json()
    analysis_te = client.get(f"/api/v1/analyses/{res_te['analysis_id']}").json()

    assert analysis_te["status"] == "completed"
    assert analysis_te["overall_lexical_coverage_percent"] > 30.0
    assert len(analysis_te["findings"]) >= 1
    assert "సాహిత్య చౌర్యం" in analysis_te["findings"][0]["submission_excerpt"]


def test_analyses_list_status_and_report_endpoints(client):
    """Tests listing analyses, polling status, and fetching summary reports."""
    # List analyses
    list_resp = client.get("/api/v1/analyses?limit=10&offset=0")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 1

    first_id = data["items"][0]["analysis_id"]

    # Poll status
    st_resp = client.get(f"/api/v1/analyses/{first_id}/status")
    assert st_resp.status_code == 200
    assert st_resp.json()["analysis_id"] == first_id

    # Get findings
    fd_resp = client.get(f"/api/v1/analyses/{first_id}/findings")
    assert fd_resp.status_code == 200
    assert isinstance(fd_resp.json(), list)

    # Get report
    rep_resp = client.get(f"/api/v1/analyses/{first_id}/report")
    assert rep_resp.status_code == 200
    rep = rep_resp.json()
    assert "disclaimer" in rep
    assert "overall_lexical_coverage_percent" in rep
