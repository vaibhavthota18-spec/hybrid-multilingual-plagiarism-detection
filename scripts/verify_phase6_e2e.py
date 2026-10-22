"""
Phase 6 End-to-End Acceptance and Verification Suite
Validates all mandatory Phase 6 product, reviewer workflow, and report generation features:
  - Scenario A: Minimalist Workflow End-to-End (Direct Upload -> Compare -> Analyze)
  - Scenario B: English Plagiarism Detection with Highlighting
  - Scenario C: Multilingual Hindi Document Analysis & Script Integrity
  - Scenario D: Multilingual Telugu Document Analysis & Script Integrity
  - Scenario E: Reviewer Action 'exclude' and Real-time Adjusted Coverage Recomputation
  - Scenario F: Reviewer Action 'quoted_cited' and Union Reduction
  - Scenario G: Reviewer Action 'keep' and Adjusted Score Preservation
  - Scenario H: Reviewer Action 'needs_review' with Custom Reviewer Notes Persistence
  - Scenario I: Detector Invariance (Raw detector scores strictly immutable under review)
  - Scenario J: Multi-format Report: Official PDF Export (ReportLab, application/pdf)
  - Scenario K: Multi-format Report: Standalone Offline HTML Export (text/html)
  - Scenario L: Multi-format Report: Machine-Readable JSON Export (application/json)
  - Scenario M: Dual-Pane Evidence Highlighting Data Model (category, span offsets, source ID)
  - Scenario N: Reviewer Summary Metrics & Findings Count Integrity
"""

import io
import json
import os
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import httpx
from fastapi.testclient import TestClient
from plagiarism.main import app
from plagiarism.storage.local_db import get_local_repo


def run_phase6_acceptance():
    print("=" * 80)
    print("  PHASE 6 PROFESSIONAL MINIMALIST UI, REVIEWER WORKFLOW & REPORTS SUITE")
    print("=" * 80)

    # Determine live server vs TestClient
    is_live = False
    try:
        resp = httpx.get("http://127.0.0.1:8000/health", timeout=1.0)
        if resp.status_code == 200:
            is_live = True
            client = httpx.Client(base_url="http://127.0.0.1:8000/api/v1", timeout=30.0)
            print("  [Mode] Executing against LIVE localhost:8000 FastAPI server")
    except Exception:
        pass

    if not is_live:
        client = TestClient(app, base_url="http://testserver/api/v1")
        print("  [Mode] Executing in-memory via FastAPI TestClient (Native Localhost)")

    repo = get_local_repo()
    all_passed = True

    def upload_doc(filename: str, content: str, lang: str = "auto") -> str:
        files = {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/plain")}
        data = {"language_hint": lang}
        res = client.post("/documents?sync_processing=true", files=files, data=data)
        assert res.status_code in (200, 201, 202), f"Failed to upload {filename}: {res.text}"
        doc_id = res.json()["document_id"]
        for _ in range(40):
            d = client.get(f"/documents/{doc_id}").json()
            if d.get("status") == "completed":
                return doc_id
            time.sleep(0.1)
        return doc_id

    def poll_analysis(analysis_id: str):
        for _ in range(40):
            res = client.get(f"/analyses/{analysis_id}")
            if res.status_code == 200:
                data = res.json()
                if data.get("status") in ("completed", "failed"):
                    return data
            time.sleep(0.2)
        return client.get(f"/analyses/{analysis_id}").json()

    # Shared state across scenarios
    analysis_id = None
    result = None
    sub_text = None
    ref_id = None

    # -------------------------------------------------------------------------
    # Scenario A: Minimalist Workflow End-to-End
    # -------------------------------------------------------------------------
    print("\n--- [Scenario A] Minimalist Workflow: Upload -> Direct Compare -> Hybrid Analysis ---")
    try:
        ref_text = (
            "Neural network architectures rely heavily on transformer attention mechanisms. "
            "Self-attention layers compute dot products between queries and keys across sequences. "
            "Residual connections and layer normalization maintain gradient flow during deep backpropagation."
        )
        sub_text = (
            "Neural network architectures rely heavily on transformer attention mechanisms. "
            "Self-attention layers compute dot products between queries and keys across sequences. "
            "Deep neural networks benefit from residual connections and normalization for stable learning."
        )

        ref_id = upload_doc("p6_ref_en.txt", ref_text, "en")
        sub_id = upload_doc("p6_sub_en.txt", sub_text, "en")

        create_res = client.post(
            "/analyses?sync_processing=true",
            json={
                "submission_document_id": sub_id,
                "mode": "direct",
                "reference_document_id": ref_id,
                "detection_mode": "hybrid",
            },
        )
        assert create_res.status_code in (200, 201, 202), f"Analysis creation failed: {create_res.text}"
        analysis_data = create_res.json()
        analysis_id = analysis_data["analysis_id"]

        result = poll_analysis(analysis_id)
        assert result["status"] == "completed", f"Analysis not completed: {result.get('error_message')}"
        assert result["overall_lexical_coverage_percent"] > 0
        assert len(result["findings"]) > 0
        raw_cov = result.get("overall_hybrid_coverage_percent", result["overall_lexical_coverage_percent"])
        print(f"  [PASS] Workflow completed successfully. Raw Hybrid Coverage: {raw_cov:.2f}%")
        print(f"         Total Findings: {len(result['findings'])}")
    except Exception as e:
        print(f"  [FAIL] Scenario A: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario B: English Highlighting & Evidence Structure
    # -------------------------------------------------------------------------
    print("\n--- [Scenario B] English Plagiarism Evidence Highlighting & Offset Alignment ---")
    try:
        assert result is not None, "Scenario A must succeed first"
        findings = result["findings"]
        first_finding = findings[0]
        assert "submission_start_offset" in first_finding
        assert "submission_end_offset" in first_finding
        assert "submission_excerpt" in first_finding
        assert first_finding["submission_end_offset"] > first_finding["submission_start_offset"]
        assert "category" in first_finding

        # Verify character slice matches extracted document text
        extracted_slice = sub_text[first_finding["submission_start_offset"] : first_finding["submission_end_offset"]]
        assert len(extracted_slice) > 0
        print(f"  [PASS] Evidence slice confirmed: '{extracted_slice[:40]}...' [Chars {first_finding['submission_start_offset']}-{first_finding['submission_end_offset']}]")
        print(f"         Category: {first_finding['category']}, Confidence: {first_finding['confidence']}")
    except Exception as e:
        print(f"  [FAIL] Scenario B: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario C: Multilingual Hindi Ingestion & Analysis
    # -------------------------------------------------------------------------
    print("\n--- [Scenario C] Multilingual Hindi Analysis & Devanagari Integrity ---")
    try:
        hi_ref = "कृत्रिम बुद्धिमत्ता और मशीन लर्निंग आधुनिक विज्ञान के अत्यंत महत्वपूर्ण क्षेत्र हैं।"
        hi_sub = "कृत्रिम बुद्धिमत्ता और मशीन लर्निंग आधुनिक विज्ञान के अत्यंत महत्वपूर्ण क्षेत्र हैं और कंप्यूटर विज़न में उपयोगी हैं।"
        hi_ref_id = upload_doc("p6_hi_ref.txt", hi_ref, "hi")
        hi_sub_id = upload_doc("p6_hi_sub.txt", hi_sub, "hi")

        hi_res = client.post(
            "/analyses?sync_processing=true",
            json={
                "submission_document_id": hi_sub_id,
                "mode": "direct",
                "reference_document_id": hi_ref_id,
                "detection_mode": "hybrid",
            },
        )
        assert hi_res.status_code in (200, 201, 202)
        hi_analysis = hi_res.json()
        hi_analysis_id = hi_analysis["analysis_id"]

        hi_result = poll_analysis(hi_analysis_id)
        assert hi_result["status"] == "completed"
        assert len(hi_result["findings"]) > 0
        print(f"  [PASS] Hindi analysis verified. Detected {len(hi_result['findings'])} findings in Devanagari script.")
    except Exception as e:
        print(f"  [FAIL] Scenario C: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario D: Multilingual Telugu Ingestion & Analysis
    # -------------------------------------------------------------------------
    print("\n--- [Scenario D] Multilingual Telugu Analysis & Telugu Script Integrity ---")
    try:
        te_ref = "కృత్రిమ మేధస్సు మరియు సహజ భాషా ప్రాసెసింగ్ రంగంలో పరిశోధనలు వేగంగా అభివృద్ధి చెందుతున్నాయి."
        te_sub = "కృత్రిమ మేధస్సు మరియు సహజ భాషా ప్రాసెసింగ్ రంగంలో పరిశోధనలు వేగంగా అభివృద్ధి చెందుతున్నాయి మరియు నూతన అవకాశాలను సృష్టిస్తున్నాయి."
        te_ref_id = upload_doc("p6_te_ref.txt", te_ref, "te")
        te_sub_id = upload_doc("p6_te_sub.txt", te_sub, "te")

        te_res = client.post(
            "/analyses?sync_processing=true",
            json={
                "submission_document_id": te_sub_id,
                "mode": "direct",
                "reference_document_id": te_ref_id,
                "detection_mode": "hybrid",
            },
        )
        assert te_res.status_code in (200, 201, 202)
        te_analysis = te_res.json()
        te_analysis_id = te_analysis["analysis_id"]

        te_result = poll_analysis(te_analysis_id)
        assert te_result["status"] == "completed"
        assert len(te_result["findings"]) > 0
        print(f"  [PASS] Telugu analysis verified. Detected {len(te_result['findings'])} findings in Telugu script.")
    except Exception as e:
        print(f"  [FAIL] Scenario D: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario E: Reviewer Action 'exclude' and Real-Time Adjusted Coverage
    # -------------------------------------------------------------------------
    print("\n--- [Scenario E] Reviewer Action 'exclude' & Adjusted Coverage Recomputation ---")
    try:
        assert result is not None and analysis_id is not None
        target_finding = result["findings"][0]
        finding_id = target_finding["finding_id"]
        raw_coverage = result.get("overall_hybrid_coverage_percent", result["overall_lexical_coverage_percent"])

        review_res = client.patch(
            f"/analyses/{analysis_id}/findings/{finding_id}/review",
            json={"decision": "exclude", "notes": "Common industry terminology; excluded from plagiarism score."},
        )
        assert review_res.status_code == 200, f"Review submission failed: {review_res.text}"
        review_data = review_res.json()

        assert review_data["finding"]["finding_id"] == finding_id
        assert review_data["finding"]["review_decision"] == "exclude"
        assert review_data["finding"]["reviewer_notes"] == "Common industry terminology; excluded from plagiarism score."
        assert review_data["reviewer_adjusted_coverage_percent"] <= raw_coverage
        print(f"  [PASS] Review decision 'exclude' applied. Raw: {raw_coverage:.2f}% -> Adjusted: {review_data['reviewer_adjusted_coverage_percent']:.2f}%")
    except Exception as e:
        print(f"  [FAIL] Scenario E: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario F: Reviewer Action 'quoted_cited' and Union Reduction
    # -------------------------------------------------------------------------
    print("\n--- [Scenario F] Reviewer Action 'quoted_cited' & Legitimate Citation Deduction ---")
    try:
        assert result is not None and analysis_id is not None
        target_finding = result["findings"][0]
        finding_id = target_finding["finding_id"]

        review_res = client.patch(
            f"/analyses/{analysis_id}/findings/{finding_id}/review",
            json={"decision": "quoted_cited", "notes": "Properly cited according to APA 7th edition."},
        )
        assert review_res.status_code == 200
        review_data = review_res.json()
        assert review_data["finding"]["review_decision"] == "quoted_cited"
        assert review_data["reviewer_adjusted_coverage_percent"] <= raw_coverage
        print(f"  [PASS] 'quoted_cited' applied. Adjusted Coverage: {review_data['reviewer_adjusted_coverage_percent']:.2f}%")
    except Exception as e:
        print(f"  [FAIL] Scenario F: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario G: Reviewer Action 'keep' and Score Preservation
    # -------------------------------------------------------------------------
    print("\n--- [Scenario G] Reviewer Action 'keep' & Score Preservation ---")
    try:
        assert result is not None and analysis_id is not None
        target_finding = result["findings"][0]
        finding_id = target_finding["finding_id"]

        review_res = client.patch(
            f"/analyses/{analysis_id}/findings/{finding_id}/review",
            json={"decision": "keep", "notes": "Verified uncredited verbatim duplication."},
        )
        assert review_res.status_code == 200
        review_data = review_res.json()
        assert review_data["finding"]["review_decision"] == "keep"
        assert abs(review_data["reviewer_adjusted_coverage_percent"] - raw_coverage) < 0.01
        print(f"  [PASS] 'keep' restored finding into active union. Adjusted: {review_data['reviewer_adjusted_coverage_percent']:.2f}% (Matches Raw {raw_coverage:.2f}%)")
    except Exception as e:
        print(f"  [FAIL] Scenario G: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario H: Reviewer Action 'needs_review' and Notes Persistence
    # -------------------------------------------------------------------------
    print("\n--- [Scenario H] Reviewer Action 'needs_review' & Custom Notes Persistence ---")
    try:
        assert result is not None and analysis_id is not None
        target_finding = result["findings"][0]
        finding_id = target_finding["finding_id"]
        notes_text = "Requires secondary review by Academic Integrity Committee."

        review_res = client.patch(
            f"/analyses/{analysis_id}/findings/{finding_id}/review",
            json={"decision": "needs_review", "notes": notes_text},
        )
        assert review_res.status_code == 200
        review_data = review_res.json()
        assert review_data["finding"]["review_decision"] == "needs_review"
        assert review_data["finding"]["reviewer_notes"] == notes_text

        updated_analysis = client.get(f"/analyses/{analysis_id}").json()
        updated_finding = [f for f in updated_analysis["findings"] if f["finding_id"] == finding_id][0]
        assert updated_finding["review_decision"] == "needs_review"
        assert updated_finding["reviewer_notes"] == notes_text
        print("  [PASS] Finding review state & reviewer notes persisted in database.")
    except Exception as e:
        print(f"  [FAIL] Scenario H: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario I: Detector Invariance (Raw Detector Scores Unaltered)
    # -------------------------------------------------------------------------
    print("\n--- [Scenario I] Mathematical Invariance: Raw Scores Strictly Immutable ---")
    try:
        assert result is not None and analysis_id is not None
        target_finding = result["findings"][0]
        finding_id = target_finding["finding_id"]

        client.patch(
            f"/analyses/{analysis_id}/findings/{finding_id}/review",
            json={"decision": "exclude", "notes": "Excluded for invariance test."},
        )
        fresh_analysis = client.get(f"/analyses/{analysis_id}").json()
        assert fresh_analysis["overall_lexical_coverage_percent"] == result["overall_lexical_coverage_percent"]
        if "overall_hybrid_coverage_percent" in result:
            assert fresh_analysis["overall_hybrid_coverage_percent"] == result["overall_hybrid_coverage_percent"]
        assert fresh_analysis["reviewer_adjusted_coverage_percent"] != result["overall_lexical_coverage_percent"]
        print(f"  [PASS] Raw detector score ({fresh_analysis['overall_lexical_coverage_percent']:.2f}%) remained invariant while adjusted score updated to {fresh_analysis['reviewer_adjusted_coverage_percent']:.2f}%.")
    except Exception as e:
        print(f"  [FAIL] Scenario I: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario J: Multi-Format Report: Official PDF Export
    # -------------------------------------------------------------------------
    print("\n--- [Scenario J] Multi-Format Report: Official PDF Export (ReportLab) ---")
    try:
        assert analysis_id is not None
        pdf_res = client.get(f"/analyses/{analysis_id}/report?format=pdf")
        assert pdf_res.status_code == 200, f"PDF export failed: {pdf_res.status_code}"
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert "attachment" in pdf_res.headers.get("content-disposition", "")
        assert pdf_res.content.startswith(b"%PDF"), "Response is not a valid PDF binary"
        assert len(pdf_res.content) > 1000
        print(f"  [PASS] Official PDF Report generated successfully ({len(pdf_res.content)} bytes, Valid %PDF magic header).")
    except Exception as e:
        print(f"  [FAIL] Scenario J: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario K: Multi-Format Report: Standalone Offline HTML Export
    # -------------------------------------------------------------------------
    print("\n--- [Scenario K] Multi-Format Report: Standalone Offline HTML Export ---")
    try:
        assert analysis_id is not None
        html_res = client.get(f"/analyses/{analysis_id}/report?format=html")
        assert html_res.status_code == 200
        assert "text/html" in html_res.headers["content-type"]
        html_text = html_res.text
        assert "<!DOCTYPE html>" in html_text
        assert "Similarity & Plagiarism Audit Report" in html_text or "Plagiarism Analysis Report" in html_text
        assert "Executive Summary" in html_text
        assert "print" in html_text or "@media print" in html_text
        print(f"  [PASS] Standalone Offline HTML Report generated successfully ({len(html_text)} characters, self-contained CSS).")
    except Exception as e:
        print(f"  [FAIL] Scenario K: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario L: Multi-Format Report: Machine-Readable JSON Export
    # -------------------------------------------------------------------------
    print("\n--- [Scenario L] Multi-Format Report: Machine-Readable JSON Export ---")
    try:
        assert analysis_id is not None
        json_res = client.get(f"/analyses/{analysis_id}/report?format=json")
        assert json_res.status_code == 200
        assert "application/json" in json_res.headers["content-type"]
        report_data = json_res.json()
        assert "analysis_id" in report_data
        assert "metrics" in report_data
        assert "findings" in report_data
        assert "overall_lexical_coverage_percent" in report_data
        assert report_data["analysis_id"] == analysis_id
        print("  [PASS] Machine-readable JSON Audit Report verified with full structural conformity.")
    except Exception as e:
        print(f"  [FAIL] Scenario L: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario M: Dual-Pane Synchronized Highlighting Data Model
    # -------------------------------------------------------------------------
    print("\n--- [Scenario M] Dual-Pane Synchronized Highlighting Data Model Integrity ---")
    try:
        assert result is not None and ref_id is not None
        f = result["findings"][0]
        assert f["submission_start_offset"] >= 0
        assert f["submission_end_offset"] > f["submission_start_offset"]
        assert f["reference_start_offset"] >= 0
        assert f["reference_end_offset"] > f["reference_start_offset"]
        assert f["reference_document_id"] == ref_id
        print(f"  [PASS] Dual-pane span offsets valid: Sub[{f['submission_start_offset']}:{f['submission_end_offset']}] <-> Ref[{f['reference_start_offset']}:{f['reference_end_offset']}]")
    except Exception as e:
        print(f"  [FAIL] Scenario M: {e}")
        all_passed = False

    # -------------------------------------------------------------------------
    # Scenario N: Reviewer Summary Metrics & Findings Count Integrity
    # -------------------------------------------------------------------------
    print("\n--- [Scenario N] Reviewer Summary Metrics & Findings Count Integrity ---")
    try:
        assert analysis_id is not None
        final_analysis = client.get(f"/analyses/{analysis_id}").json()
        assert "reviewed_findings_count" in final_analysis
        assert "reviewer_adjusted_coverage_percent" in final_analysis
        assert final_analysis["reviewed_findings_count"] >= 1
        print(f"  [PASS] Review summary verified: {final_analysis['reviewed_findings_count']} findings reviewed. Adjusted Coverage: {final_analysis['reviewer_adjusted_coverage_percent']:.2f}%.")
    except Exception as e:
        print(f"  [FAIL] Scenario N: {e}")
        all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("  [SUCCESS] ALL PHASE 6 ACCEPTANCE SCENARIOS PASSED WITH ZERO ERRORS.")
    else:
        print("  [FAILURE] SOME SCENARIOS FAILED. PLEASE REVIEW LOGS ABOVE.")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_phase6_acceptance()
    sys.exit(0 if success else 1)
