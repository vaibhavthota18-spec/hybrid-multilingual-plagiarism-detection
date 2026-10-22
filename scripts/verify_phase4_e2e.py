"""
Phase 4 End-to-End Acceptance Verification Suite
Validates all mandatory Phase 4 scenarios (A through N) for Multilingual Semantic AI,
Vector Embeddings, Cross-Language Retrieval, and Hybrid Plagiarism Detection:
  - Scenario A: Lexical Baseline Regression (Verbatim copying detected accurately)
  - Scenario B: English Paraphrase Detection (Dense semantic match >= 0.82)
  - Scenario C: Hard Negative / Unrelated Rejection (Filtered out below threshold)
  - Scenario D: Multilingual Hindi Paraphrase Detection (Devanagari semantic match >= 0.82)
  - Scenario E: Multilingual Telugu Paraphrase Detection (Telugu semantic match >= 0.82)
  - Scenario F: Cross-Language English <-> Hindi Retrieval (Potential translation match >= 0.80)
  - Scenario G: Cross-Language English <-> Telugu Retrieval (Potential translation match >= 0.80)
  - Scenario H: Hybrid Detection & Non-Overlapping Coverage (Verbatim + Paraphrase union)
  - Scenario I: One-to-Many Comparison Mode (Dense retrieval across candidate reference pool)
  - Scenario J: Corpus Mode (Collection-based candidate retrieval + semantic ranking)
  - Scenario K: SQLite BLOB Vector Persistence Across Reboot (Durability check)
  - Scenario L: Foreign Key Cascade Deletion (Passage vector records purged on doc removal)
  - Scenario M: Model-Aware Sentence-Boundary Segmentation (Token sequence budget adherence)
  - Scenario N: Model Metadata & Runtime Device Endpoint (/analyses/models/info)
"""

import io
import json
import os
import sys
import time
import uuid
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import httpx
from fastapi.testclient import TestClient
from plagiarism.main import app
from plagiarism.storage.local_db import get_local_repo, LocalMetadataRepository
from plagiarism.storage.vector_store import SQLiteVectorRepository, PassageVectorRecord
from plagiarism.services.semantic.provider import get_embedding_provider
from plagiarism.services.semantic.segmentation import ModelAwareSegmenter
from plagiarism.core.config import get_settings


def run_phase4_acceptance():
    print("=" * 80)
    print("  PHASE 4 HYBRID AI & MULTILINGUAL SEMANTIC PLAGIARISM ACCEPTANCE SUITE")
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
        print("  [Mode] Executing directly via FastAPI TestClient harness")

    settings = get_settings()
    repo = get_local_repo()
    provider = get_embedding_provider()
    segmenter = ModelAwareSegmenter()

    passed_scenarios = 0
    total_scenarios = 14

    def upload_doc(filename: str, content: str, title: str) -> str:
        res = client.post(
            "/documents?sync_processing=true",
            files={"file": (filename, io.BytesIO(content.encode("utf-8")), "text/plain")},
            data={"title": title},
        )
        assert res.status_code == 201, f"Failed to upload document {filename}: {res.text}"
        return res.json()["document_id"]

    def cleanup_doc(doc_id: str):
        client.delete(f"/documents/{doc_id}")

    # =========================================================================
    # Scenario A: Lexical Baseline Regression
    # =========================================================================
    print("\n--- [Scenario A] Lexical Baseline Regression (Verbatim Copying) ---")
    doc_ref_a = upload_doc(
        "ref_a.txt",
        "Deterministic winnowing produces fingerprint hashes that guarantee detection of any substring match.",
        "Ref A",
    )
    doc_sub_a = upload_doc(
        "sub_a.txt",
        "Deterministic winnowing produces fingerprint hashes that guarantee detection of any substring match.",
        "Sub A",
    )
    res_a = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_a,
            "reference_document_id": doc_ref_a,
            "mode": "direct",
            "detection_mode": "lexical",
        },
    )
    assert res_a.status_code == 202
    an_a = client.get(f"/analyses/{res_a.json()['analysis_id']}").json()
    assert an_a["status"] == "completed"
    assert an_a["overall_lexical_coverage_percent"] > 90.0
    print(f"  [PASS] Lexical coverage: {an_a['overall_lexical_coverage_percent']:.1f}%, Findings: {len(an_a['findings'])}")
    passed_scenarios += 1
    cleanup_doc(doc_ref_a)
    cleanup_doc(doc_sub_a)

    # =========================================================================
    # Scenario B: English Paraphrase Detection
    # =========================================================================
    print("\n--- [Scenario B] English Paraphrase Detection ---")
    doc_ref_b = upload_doc(
        "ref_b.txt",
        "Deep neural networks have revolutionized natural language understanding through transformer attention mechanisms and self-supervised pretraining.",
        "Ref B",
    )
    doc_sub_b = upload_doc(
        "sub_b.txt",
        "Modern deep learning architectures transformed natural language processing by utilizing attention layers and self-supervised training strategies.",
        "Sub B",
    )
    res_b = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_b,
            "reference_document_id": doc_ref_b,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_b.status_code == 202
    an_b = client.get(f"/analyses/{res_b.json()['analysis_id']}").json()
    assert an_b["status"] == "completed"
    assert len(an_b["findings"]) >= 1
    assert an_b["findings"][0]["category"] == "paraphrase"
    assert an_b["findings"][0]["semantic_similarity"] >= settings.SEMANTIC_PARAPHRASE_THRESHOLD
    print(f"  [PASS] Paraphrase detected with Cosine: {an_b['findings'][0]['semantic_similarity']:.4f} (Threshold: {settings.SEMANTIC_PARAPHRASE_THRESHOLD})")
    passed_scenarios += 1
    cleanup_doc(doc_ref_b)
    cleanup_doc(doc_sub_b)

    # =========================================================================
    # Scenario C: Hard Negative / Unrelated Rejection
    # =========================================================================
    print("\n--- [Scenario C] Hard Negative / Unrelated Rejection ---")
    doc_ref_c = upload_doc(
        "ref_c.txt",
        "Convolutional neural networks extract hierarchical spatial representations from raster images.",
        "Ref C",
    )
    doc_sub_c = upload_doc(
        "sub_c.txt",
        "Artisanal sourdough bread requires precise water temperature, whole grain flour, and overnight fermentation.",
        "Sub C",
    )
    res_c = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_c,
            "reference_document_id": doc_ref_c,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_c.status_code == 202
    an_c = client.get(f"/analyses/{res_c.json()['analysis_id']}").json()
    assert an_c["status"] == "completed"
    assert len(an_c["findings"]) == 0
    assert an_c["overall_semantic_coverage_percent"] == 0.0
    print("  [PASS] Hard negative rejected. Zero false positive findings produced.")
    passed_scenarios += 1
    cleanup_doc(doc_ref_c)
    cleanup_doc(doc_sub_c)

    # =========================================================================
    # Scenario D: Multilingual Hindi Paraphrase Detection
    # =========================================================================
    print("\n--- [Scenario D] Multilingual Hindi Paraphrase Detection ---")
    doc_ref_d = upload_doc(
        "ref_d.txt",
        "साहित्यिक चोरी शैक्षणिक अखंडता और अनुसंधान के मानकों का उल्लंघन करती है।",
        "Ref D (Hindi)",
    )
    doc_sub_d = upload_doc(
        "sub_d.txt",
        "अनुसंधान में दूसरों के विचारों को बिना श्रेय दिए उपयोग करना शैक्षणिक सत्यनिष्ठा और आचार संहिता का सीधा हनन है।",
        "Sub D (Hindi)",
    )
    res_d = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_d,
            "reference_document_id": doc_ref_d,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_d.status_code == 202
    an_d = client.get(f"/analyses/{res_d.json()['analysis_id']}").json()
    assert an_d["status"] == "completed"
    assert len(an_d["findings"]) >= 1
    assert an_d["findings"][0]["category"] == "paraphrase"
    assert an_d["findings"][0]["semantic_similarity"] >= settings.SEMANTIC_PARAPHRASE_THRESHOLD
    print(f"  [PASS] Hindi paraphrase detected with Cosine: {an_d['findings'][0]['semantic_similarity']:.4f}")
    passed_scenarios += 1
    cleanup_doc(doc_ref_d)
    cleanup_doc(doc_sub_d)

    # =========================================================================
    # Scenario E: Multilingual Telugu Paraphrase Detection
    # =========================================================================
    print("\n--- [Scenario E] Multilingual Telugu Paraphrase Detection ---")
    doc_ref_e = upload_doc(
        "ref_e.txt",
        "కృత్రిమ మేధస్సు మరియు యంత్ర అభ్యాసం ఆధునిక సాంకేతిక విప్లవానికి పునాదిగా నిలుస్తున్నాయి.",
        "Ref E (Telugu)",
    )
    doc_sub_e = upload_doc(
        "sub_e.txt",
        "నేటి సాంకేతిక మార్పులకు ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ మరియు మెషిన్ లెర్నింగ్ కీలక చోదక శక్తులుగా మారాయి.",
        "Sub E (Telugu)",
    )
    res_e = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_e,
            "reference_document_id": doc_ref_e,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_e.status_code == 202
    an_e = client.get(f"/analyses/{res_e.json()['analysis_id']}").json()
    assert an_e["status"] == "completed"
    assert len(an_e["findings"]) >= 1
    assert an_e["findings"][0]["category"] == "paraphrase"
    assert an_e["findings"][0]["semantic_similarity"] >= settings.SEMANTIC_PARAPHRASE_THRESHOLD
    print(f"  [PASS] Telugu paraphrase detected with Cosine: {an_e['findings'][0]['semantic_similarity']:.4f}")
    passed_scenarios += 1
    cleanup_doc(doc_ref_e)
    cleanup_doc(doc_sub_e)

    # =========================================================================
    # Scenario F: Cross-Language English <-> Hindi Retrieval
    # =========================================================================
    print("\n--- [Scenario F] Cross-Language English <-> Hindi Retrieval ---")
    doc_ref_f = upload_doc(
        "ref_f.txt",
        "Quantum computing utilizes quantum superposition and entanglement to solve complex mathematical problems.",
        "Ref F (English)",
    )
    doc_sub_f = upload_doc(
        "sub_f.txt",
        "क्वांटम कंप्यूटिंग जटिल गणितीय समस्याओं को हल करने के लिए क्वांटम सुपरपोजिशन और एंटैंगलमेंट का उपयोग करती है।",
        "Sub F (Hindi)",
    )
    res_f = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_f,
            "reference_document_id": doc_ref_f,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_f.status_code == 202
    an_f = client.get(f"/analyses/{res_f.json()['analysis_id']}").json()
    assert an_f["status"] == "completed"
    assert len(an_f["findings"]) >= 1
    assert an_f["findings"][0]["category"] == "potential_translation"
    assert an_f["findings"][0]["semantic_similarity"] >= settings.SEMANTIC_TRANSLATION_THRESHOLD
    assert an_f["findings"][0]["language_pair"] == "hi-en"
    print(f"  [PASS] Cross-lingual HI->EN detected with Cosine: {an_f['findings'][0]['semantic_similarity']:.4f}, Category: {an_f['findings'][0]['category']}")
    passed_scenarios += 1
    cleanup_doc(doc_ref_f)
    cleanup_doc(doc_sub_f)

    # =========================================================================
    # Scenario G: Cross-Language English <-> Telugu Retrieval
    # =========================================================================
    print("\n--- [Scenario G] Cross-Language English <-> Telugu Retrieval ---")
    doc_ref_g = upload_doc(
        "ref_g.txt",
        "Solar panels convert incident sunlight into renewable electrical energy using photovoltaic cells.",
        "Ref G (English)",
    )
    doc_sub_g = upload_doc(
        "sub_g.txt",
        "సౌర ఫలకాలు ఫోటోవోల్టాయిక్ కణాల ద్వారా సూర్యకాంతిని పునరుత్పాదక విద్యుత్ శక్తిగా మారుస్తాయి.",
        "Sub G (Telugu)",
    )
    res_g = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_g,
            "reference_document_id": doc_ref_g,
            "mode": "direct",
            "detection_mode": "semantic",
        },
    )
    assert res_g.status_code == 202
    an_g = client.get(f"/analyses/{res_g.json()['analysis_id']}").json()
    assert an_g["status"] == "completed"
    assert len(an_g["findings"]) >= 1
    assert an_g["findings"][0]["category"] == "potential_translation"
    assert an_g["findings"][0]["semantic_similarity"] >= settings.SEMANTIC_TRANSLATION_THRESHOLD
    assert an_g["findings"][0]["language_pair"] == "te-en"
    print(f"  [PASS] Cross-lingual TE->EN detected with Cosine: {an_g['findings'][0]['semantic_similarity']:.4f}, Category: {an_g['findings'][0]['category']}")
    passed_scenarios += 1
    cleanup_doc(doc_ref_g)
    cleanup_doc(doc_sub_g)

    # =========================================================================
    # Scenario H: Hybrid Detection & Non-Overlapping Coverage
    # =========================================================================
    print("\n--- [Scenario H] Hybrid Detection & Non-Overlapping Coverage ---")
    doc_ref_h = upload_doc(
        "ref_h.txt",
        "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose. Chlorophyll absorbs solar radiation across visible wavelengths.",
        "Ref H",
    )
    doc_sub_h = upload_doc(
        "sub_h.txt",
        "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules such as glucose. Plant chloroplasts harness the power of sunlight to generate vital organic sugars.",
        "Sub H",
    )
    res_h = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_h,
            "reference_document_id": doc_ref_h,
            "mode": "direct",
            "detection_mode": "hybrid",
        },
    )
    assert res_h.status_code == 202
    an_h = client.get(f"/analyses/{res_h.json()['analysis_id']}").json()
    assert an_h["status"] == "completed"
    assert an_h["detection_mode"] == "hybrid"
    assert an_h["overall_lexical_coverage_percent"] > 0
    assert an_h["overall_semantic_coverage_percent"] > 0
    assert an_h["hybrid_evidence_coverage_percent"] >= an_h["overall_lexical_coverage_percent"]
    assert an_h["net_adjusted_score_percent"] > 0
    print(f"  [PASS] Hybrid Net Score: {an_h['net_adjusted_score_percent']}%, Lexical Cov: {an_h['overall_lexical_coverage_percent']}%, Semantic Cov: {an_h['overall_semantic_coverage_percent']}%, Union Cov: {an_h['hybrid_evidence_coverage_percent']}%")
    passed_scenarios += 1
    cleanup_doc(doc_ref_h)
    cleanup_doc(doc_sub_h)

    # =========================================================================
    # Scenario I: One-to-Many Comparison Mode
    # =========================================================================
    print("\n--- [Scenario I] One-to-Many Comparison Mode ---")
    doc_ref_i1 = upload_doc(
        "ref_i1.txt",
        "Deep neural networks have revolutionized natural language understanding through transformer attention mechanisms and self-supervised pretraining.",
        "Ref I1 (NLP)",
    )
    doc_ref_i2 = upload_doc(
        "ref_i2.txt",
        "Photosynthesis in green plants converts light energy into chemical energy stored in carbohydrate molecules.",
        "Ref I2 (Bio)",
    )
    doc_sub_i = upload_doc(
        "sub_i.txt",
        "Modern deep learning architectures transformed natural language processing by utilizing attention layers.",
        "Sub I",
    )
    res_i = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_i,
            "reference_document_ids": [doc_ref_i1, doc_ref_i2],
            "mode": "one_to_many",
            "detection_mode": "hybrid",
        },
    )
    assert res_i.status_code == 202
    an_i = client.get(f"/analyses/{res_i.json()['analysis_id']}").json()
    assert an_i["status"] == "completed"
    assert len(an_i["findings"]) >= 1
    matched_refs = {f["reference_document_id"] for f in an_i["findings"]}
    assert doc_ref_i1 in matched_refs
    assert doc_ref_i2 not in matched_refs
    print(f"  [PASS] Successfully retrieved relevant reference from candidate pool. Matched Ref: {doc_ref_i1[:8]}...")
    passed_scenarios += 1
    cleanup_doc(doc_ref_i1)
    cleanup_doc(doc_ref_i2)
    cleanup_doc(doc_sub_i)

    # =========================================================================
    # Scenario J: Corpus Mode (Collection Search)
    # =========================================================================
    print("\n--- [Scenario J] Corpus Mode with Collection Filtering ---")
    col_resp = client.post(
        "/collections",
        json={"name": "Academic Papers Collection", "description": "Benchmark collection for corpus search"},
    )
    assert col_resp.status_code == 201
    col_id = col_resp.json()["collection_id"]

    doc_ref_j = upload_doc(
        "ref_j.txt",
        "Database indexing enables rapid querying, search efficiency, and data retrieval across large storage volumes.",
        "Ref J",
    )
    add_doc_resp = client.post(
        f"/collections/{col_id}/documents",
        json={"document_id": doc_ref_j},
    )
    assert add_doc_resp.status_code == 201

    doc_sub_j = upload_doc(
        "sub_j.txt",
        "డేటాబేస్ ఇండెక్సింగ్ ద్వారా సమాచారాన్ని వేగంగా శోధించడం మరియు తిరిగి పొందడం సాధ్యమవుతుంది.",
        "Sub J (Telugu translation)",
    )

    res_j = client.post(
        "/analyses?sync_processing=true",
        json={
            "submission_document_id": doc_sub_j,
            "collection_id": col_id,
            "mode": "corpus",
            "detection_mode": "hybrid",
        },
    )
    assert res_j.status_code == 202
    an_j = client.get(f"/analyses/{res_j.json()['analysis_id']}").json()
    assert an_j["status"] == "completed"
    assert len(an_j["findings"]) >= 1
    print(f"  [PASS] Corpus mode retrieved collection document with {len(an_j['findings'])} finding(s)")
    passed_scenarios += 1
    client.delete(f"/collections/{col_id}")
    cleanup_doc(doc_ref_j)
    cleanup_doc(doc_sub_j)

    # =========================================================================
    # Scenario K: SQLite BLOB Vector Persistence Across Reboot
    # =========================================================================
    print("\n--- [Scenario K] SQLite BLOB Vector Persistence Across Reboot ---")
    doc_k_id = str(uuid.uuid4())
    repo.insert_document(
        document_id=doc_k_id,
        owner_user_id="00000000-0000-0000-0000-000000000001",
        filename="reboot_test.txt",
        mime_type="text/plain",
        sha256_hash="hash_reboot_k",
        storage_path="storage/private/reboot.txt",
        file_size_bytes=120,
        status="completed",
        title="Reboot Test",
    )
    test_vec = provider.encode_passages(["Persistence test passage across process instances."])[0]
    import hashlib
    from datetime import datetime, timezone

    rec_k = PassageVectorRecord(
        passage_id=f"{doc_k_id}_p0",
        document_id=doc_k_id,
        sequence_index=0,
        start_offset=0,
        end_offset=50,
        text_content="Persistence test passage across process instances.",
        model_id="intfloat/multilingual-e5-small",
        model_revision="614241f622f53c4eeff9890bdc4f31cfecc418b3",
        embedding=test_vec,
        text_hash=hashlib.sha256(b"Persistence test passage across process instances.").hexdigest(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    v_repo1 = SQLiteVectorRepository(repo=repo)
    v_repo1.store_document_embeddings([rec_k])

    # Re-instantiate repo simulates reboot / cold start
    v_repo2 = SQLiteVectorRepository(repo=LocalMetadataRepository())
    stored_recs = v_repo2.get_document_embeddings(doc_k_id)
    assert len(stored_recs) == 1
    assert stored_recs[0].embedding.shape == (384,)
    assert np.allclose(stored_recs[0].embedding, test_vec, atol=1e-5)
    print("  [PASS] Stored binary BLOB embedding survived fresh instance reload with exact float32 fidelity.")
    passed_scenarios += 1

    # =========================================================================
    # Scenario L: Foreign Key Cascade Deletion
    # =========================================================================
    print("\n--- [Scenario L] Foreign Key Cascade Deletion of Passage Embeddings ---")
    repo.delete_document(doc_k_id)
    stored_after_del = v_repo2.get_document_embeddings(doc_k_id)
    assert len(stored_after_del) == 0
    print("  [PASS] Deleting document cascaded to passage_embeddings table. Records count: 0.")
    passed_scenarios += 1

    # =========================================================================
    # Scenario M: Model-Aware Sentence-Boundary Segmentation
    # =========================================================================
    print("\n--- [Scenario M] Model-Aware Sentence-Boundary Segmentation ---")
    long_en_sentence = "Natural language processing systems utilize token sequence architectures for contextual representations. " * 8
    long_passages = segmenter.prepare_passages(
        document_id="long_doc_1",
        original_text=long_en_sentence,
        detected_language="en",
    )
    assert len(long_passages) >= 1
    for p in long_passages:
        assert p.token_count <= segmenter.max_tokens
        assert long_en_sentence[p.start_offset:p.end_offset].strip() == p.text_content.strip()
    print(f"  [PASS] Oversized text segmented into {len(long_passages)} chunks, all <= {segmenter.max_tokens} tokens with exact offsets.")
    passed_scenarios += 1

    # =========================================================================
    # Scenario N: Model Metadata & Runtime Device Endpoint
    # =========================================================================
    print("\n--- [Scenario N] Model Metadata & Runtime Device Endpoint ---")
    info_resp = client.get("/analyses/models/info")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert "multilingual-e5-small" in info_data["model_name"]
    assert info_data["embedding_dimension"] == 384
    assert info_data["max_sequence_length"] == 512
    assert info_data["paraphrase_threshold"] == 0.82
    assert info_data["translation_threshold"] == 0.80
    assert info_data["runtime_device"] in ("cpu", "cuda")
    print(f"  [PASS] Active Model: {info_data['model_name']}, Dim: {info_data['embedding_dimension']}, Device: {info_data['runtime_device']}")
    passed_scenarios += 1

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"  PHASE 4 ACCEPTANCE RESULT: {passed_scenarios}/{total_scenarios} SCENARIOS PASSED (100%)")
    print("=" * 80)
    return passed_scenarios == total_scenarios


if __name__ == "__main__":
    success = run_phase4_acceptance()
    sys.exit(0 if success else 1)
