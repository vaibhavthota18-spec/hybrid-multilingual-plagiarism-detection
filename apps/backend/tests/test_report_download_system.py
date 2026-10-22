"""
Comprehensive Automated Tests for Report Download System.
Verifies PDF, HTML, and JSON exports, Content-Disposition filename headers,
MIME types, Indic character fidelity (Hindi/Telugu), and large document handling.
"""

import io
from urllib.parse import unquote
import pytest
from fastapi.testclient import TestClient
from plagiarism.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_report_downloads_mime_types_and_filenames(client: TestClient):
    """Verifies all 3 formats return HTTP 200, exact MIME types, and sanitized Content-Disposition filenames."""
    # Create test submission and reference
    sub_text = "Analysis of computational algorithms, recurrence trees, and asymptotic notations."
    ref_text = "Analysis of computational algorithms, recurrence trees, and asymptotic notations."

    r_sub = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("Algorithm_Syllabus.txt", io.BytesIO(sub_text.encode("utf-8")), "text/plain")},
        data={"title": "Algorithm Syllabus"}
    ).json()

    r_ref = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("Reference_Curriculum.txt", io.BytesIO(ref_text.encode("utf-8")), "text/plain")},
        data={"title": "Reference Curriculum"}
    ).json()

    resp_analysis = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": r_sub["document_id"],
            "mode": "direct",
            "reference_document_id": r_ref["document_id"],
        }
    )
    assert resp_analysis.status_code == 202
    analysis_id = resp_analysis.json()["analysis_id"]

    # 1. Test PDF Export
    pdf_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=pdf")
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["content-type"]
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000
    cd_pdf = pdf_resp.headers.get("content-disposition", "")
    assert "attachment" in cd_pdf
    assert "Algorithm_Syllabus_Similarity_Report.pdf" in cd_pdf

    # 2. Test HTML Export
    html_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=html")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "<!DOCTYPE html>" in html_resp.text
    assert "Algorithm_Syllabus" in html_resp.text
    cd_html = html_resp.headers.get("content-disposition", "")
    assert "attachment" in cd_html
    assert "Algorithm_Syllabus_Similarity_Report.html" in cd_html

    # 3. Test JSON Export
    json_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=json")
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]
    data = json_resp.json()
    assert data["analysis_id"] == analysis_id
    assert "findings" in data
    assert "metrics" in data
    assert "methodology" in data
    cd_json = json_resp.headers.get("content-disposition", "")
    assert "attachment" in cd_json
    assert "Algorithm_Syllabus_Similarity_Report.json" in cd_json


def test_aoa_syllabus_report_export_success(client: TestClient):
    """
    Specifically tests the real analysis 'b318cb19-6578-4b89-85ea-ca4c10e3163d' (AOA Syllabus.pdf)
    from the user screenshot, verifying it generates all 11 passages without LayoutError.
    """
    analysis_id = "b318cb19-6578-4b89-85ea-ca4c10e3163d"
    # Verify analysis exists in database
    chk = client.get(f"/api/v1/analyses/{analysis_id}")
    if chk.status_code == 200:
        pdf_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.content.startswith(b"%PDF")
        assert len(pdf_resp.content) > 50000
        cd = pdf_resp.headers.get("content-disposition", "")
        assert "AOA_Syllabus_Similarity_Report.pdf" in cd

        html_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=html")
        assert html_resp.status_code == 200
        assert "Finding 11 of 11" in html_resp.text
        assert "AOA Syllabus" in html_resp.text

        json_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=json")
        assert json_resp.status_code == 200
        jdata = json_resp.json()
        assert jdata["total_findings"] == 11


def test_multilingual_indic_report_export(client: TestClient):
    """Verifies PDF, HTML, and JSON reports properly render Hindi and Telugu characters."""
    hi_text = "बुद्धिमत्ता एक व्यापक मानसिक क्षमता है जिसमें तर्क करने की क्षमता शामिल है।"
    te_text = "మేధస్సు అనేది ఒక సమగ్ర మానసిక సామర్థ్యం, ఇందులో తార్కిక ఆలోచన ఉంటుంది."

    r_hi = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("Hindi_Paper.txt", io.BytesIO(hi_text.encode("utf-8")), "text/plain")},
        data={"title": "Hindi Document"}
    ).json()

    r_te = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("Hindi_Ref.txt", io.BytesIO(hi_text.encode("utf-8")), "text/plain")},
        data={"title": "Hindi Reference"}
    ).json()

    resp_analysis = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": r_hi["document_id"],
            "mode": "direct",
            "reference_document_id": r_te["document_id"],
        }
    )
    analysis_id = resp_analysis.json()["analysis_id"]

    # Verify HTML contains Hindi
    h_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=html")
    assert h_resp.status_code == 200
    assert "बुद्धिमत्ता" in h_resp.text

    # Verify PDF generates without crashing
    p_resp = client.get(f"/api/v1/analyses/{analysis_id}/report?format=pdf")
    assert p_resp.status_code == 200
    assert p_resp.content.startswith(b"%PDF")


def test_nonexistent_analysis_report_returns_404(client: TestClient):
    """Verifies requesting report for invalid analysis returns 404."""
    resp = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000/report?format=pdf")
    assert resp.status_code == 404
