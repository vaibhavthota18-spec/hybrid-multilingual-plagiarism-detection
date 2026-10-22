"""
Phase 4 Semantic AI & Hybrid Detection Unit & Integration Tests.
Tests:
1. LocalSentenceTransformerProvider (embeddings, dimensions, normalization, prefixes, determinism).
2. ModelAwareSegmenter (token budget, Unicode offsets, Hindi/Telugu).
3. SQLiteVectorRepository (binary BLOB storage, cosine similarity search, cascade deletion).
4. SemanticMatcher (EN paraphrase, HI paraphrase, TE paraphrase, cross-lingual retrieval, hard negatives).
5. HybridAnalysisService (lexical, semantic, hybrid modes, union coverage, deduplication).
6. Analyses API endpoints (/analyses/models/info, POST /analyses with detection_mode).
"""

import uuid
from datetime import UTC

import numpy as np
import pytest
from fastapi.testclient import TestClient

from plagiarism.core.config import get_settings
from plagiarism.main import app
from plagiarism.services.hybrid_service import get_hybrid_service
from plagiarism.services.semantic.matcher import SemanticMatcher
from plagiarism.services.semantic.provider import (
    get_embedding_provider,
)
from plagiarism.services.semantic.segmentation import ModelAwareSegmenter
from plagiarism.storage.local_db import get_local_repo
from plagiarism.storage.vector_store import (
    PassageVectorRecord,
    SQLiteVectorRepository,
)


def _insert_test_doc(repo, doc_id: str, filename: str, text: str, lang: str = "en"):
    repo.insert_document(
        document_id=doc_id,
        owner_user_id="00000000-0000-0000-0000-000000000001",
        filename=filename,
        mime_type="text/plain",
        sha256_hash=f"hash_{doc_id}",
        storage_path=f"storage/private/{doc_id}.txt",
        file_size_bytes=len(text.encode("utf-8")),
        status="completed",
        title=filename,
    )
    repo.update_document_extraction(
        document_id=doc_id,
        status="completed",
        page_count=1,
        char_count=len(text),
        word_count=len(text.split()),
        raw_text=text,
        detected_language=lang,
        warnings="",
    )


def _delete_test_doc(repo, doc_id: str):
    repo.delete_document(doc_id)


@pytest.fixture(scope="module")
def provider():
    """Module-level fixture to load the provider once for tests."""
    return get_embedding_provider()


@pytest.fixture(scope="module")
def segmenter():
    """Module-level segmenter fixture."""
    return ModelAwareSegmenter()


@pytest.fixture
def client():
    return TestClient(app)


def test_provider_embedding_dimensions_and_normalization(provider):
    """Verifies embedding dimension is exactly 384 and vectors are L2-normalized."""
    texts = [
        "This is an academic research paper on artificial intelligence.",
        "यह कंप्यूटर विज्ञान और प्राकृतिक भाषा प्रसंस्करण पर एक शोध पत्र है।",
    ]
    query_vecs = provider.encode_queries(texts)
    assert query_vecs.shape == (2, 384)
    assert query_vecs.dtype == np.float32

    # L2 norm must be approximately 1.0
    for vec in query_vecs:
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-4

    passage_vecs = provider.encode_passages(texts)
    assert passage_vecs.shape == (2, 384)
    for vec in passage_vecs:
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-4


def test_provider_prefix_handling_and_determinism(provider):
    """Verifies that query prefix and passage prefix produce distinct but deterministic vectors."""
    text = "Machine learning architectures are advancing rapidly."

    q1 = provider.encode_queries([text])[0]
    q2 = provider.encode_queries([text])[0]
    p1 = provider.encode_passages([text])[0]

    # Deterministic
    assert np.allclose(q1, q2, atol=1e-5)
    # Distinct prefixes produce distinct embeddings
    assert not np.allclose(q1, p1, atol=1e-3)
    # Cosine between query and passage encoding of the same text is high
    dot_product = float(np.dot(q1, p1))
    assert dot_product > 0.85


def test_provider_empty_input(provider):
    """Verifies safe empty input handling."""
    res = provider.encode_queries([])
    assert len(res) == 0
    assert res.shape == (0, 384)


def test_provider_model_info(provider):
    """Verifies model metadata dictionary."""
    info = provider.get_model_info()
    assert "multilingual-e5-small" in info["model_name"]
    assert info["embedding_dimension"] == 384
    assert info["max_sequence_length"] == 512
    assert "model_path" in info


def test_model_aware_segmenter_token_budget(segmenter):
    """Verifies that segmenter respects token count and preserves offsets."""
    text = (
        "Academic dishonesty undermines research credibility and educational standards. "
        "Plagiarism in academic institutions causes significant harm to scientific integrity. "
        "Automatic detection tools help educators identify unauthorized copying. "
    )
    doc_id = str(uuid.uuid4())
    passages = segmenter.prepare_passages(
        document_id=doc_id,
        original_text=text,
        detected_language="en",
    )
    assert len(passages) >= 1
    for p in passages:
        assert p.token_count <= segmenter.max_tokens
        assert p.document_id == doc_id
        # Verify text slice matches original text
        assert text[p.start_offset:p.end_offset].strip() == p.text_content.strip()


def test_model_aware_segmenter_multilingual_indic(segmenter):
    """Verifies segmenter correctly handles Hindi and Telugu scripts."""
    hi_text = (
        "साहित्यिक चोरी एक गंभीर शैक्षणिक अपराध है। "
        "यह शोधकर्ताओं के नैतिक मूल्यों और सत्यनिष्ठा को प्रभावित करती है। "
        "एआई आधारित प्रणाली इसे आसानी से पहचान सकती है।"
    )
    passages_hi = segmenter.prepare_passages(
        document_id="hi_doc_1",
        original_text=hi_text,
        detected_language="hi",
    )
    assert len(passages_hi) >= 1
    assert passages_hi[0].language == "hi"
    assert hi_text[passages_hi[0].start_offset:passages_hi[0].end_offset] == passages_hi[0].text_content

    te_text = (
        "విద్యాసంబంధ పరిశోధనలలో నిజాయితీ ఎంతో ముఖ్యమైనది. "
        "సాహిత్య చోర్యం పరిశోధన ప్రమాణాలను దెబ్బతీస్తుంది. "
        "ఆధునిక కంప్యూటర్ వ్యవస్థలు దీన్ని గుర్తించగలవు."
    )
    passages_te = segmenter.prepare_passages(
        document_id="te_doc_1",
        original_text=te_text,
        detected_language="te",
    )
    assert len(passages_te) >= 1
    assert passages_te[0].language == "te"
    assert te_text[passages_te[0].start_offset:passages_te[0].end_offset] == passages_te[0].text_content


def test_sqlite_vector_repository_crud_and_search(provider):
    """Verifies binary BLOB serialization, storage, cosine search, and cascade deletion."""
    db_repo = get_local_repo()
    repo = SQLiteVectorRepository()
    doc_id = str(uuid.uuid4())

    # Create dummy document in metadata DB
    _insert_test_doc(
        db_repo,
        doc_id=doc_id,
        filename="vector_test.txt",
        text="Quantum computing utilizes quantum superposition and entanglement to solve complex problems.",
        lang="en",
    )

    import hashlib
    from datetime import datetime

    vec = provider.encode_passages(["Quantum computing utilizes quantum superposition and entanglement."])[0]
    rec = PassageVectorRecord(
        passage_id=f"{doc_id}_p0",
        document_id=doc_id,
        sequence_index=0,
        start_offset=0,
        end_offset=68,
        text_content="Quantum computing utilizes quantum superposition and entanglement.",
        model_id="intfloat/multilingual-e5-small",
        model_revision="614241f622f53c4eeff9890bdc4f31cfecc418b3",
        embedding=vec,
        text_hash=hashlib.sha256(b"Quantum computing utilizes quantum superposition and entanglement.").hexdigest(),
        created_at=datetime.now(UTC).isoformat(),
    )
    repo.store_document_embeddings([rec])

    # Search for matching query
    query_vec = provider.encode_queries(["How does quantum computing use superposition?"])
    results = repo.search_candidates(
        query_vectors=query_vec,
        candidate_document_ids=[doc_id],
        top_k=3,
        min_similarity=0.60,
    )

    assert len(results) == 1
    assert len(results[0]) >= 1
    hit = results[0][0]
    assert hit.reference_document_id == doc_id
    assert hit.cosine_similarity > 0.80
    assert "superposition" in hit.reference_text_content

    # Clean up document and verify cascade deletion of vector embeddings
    _delete_test_doc(db_repo, doc_id)
    embeddings_after_del = repo.get_document_embeddings(doc_id)
    assert len(embeddings_after_del) == 0


def test_semantic_matcher_multilingual_and_hard_negatives(provider, segmenter):
    """
    Verifies SemanticMatcher identifies genuine paraphrases and translations
    while strictly filtering out hard negatives below the calibrated threshold.
    """
    db_repo = get_local_repo()
    settings = get_settings()
    repo = SQLiteVectorRepository()
    matcher = SemanticMatcher(provider=provider, vector_repo=repo, segmenter=segmenter)

    ref_doc_id = str(uuid.uuid4())
    ref_text = (
        "Deep neural networks have revolutionized natural language understanding through "
        "transformer attention mechanisms and self-supervised pretraining."
    )
    _insert_test_doc(
        db_repo,
        doc_id=ref_doc_id,
        filename="nlp_reference.txt",
        text=ref_text,
        lang="en",
    )

    candidate_docs = [
        {
            "document_id": ref_doc_id,
            "filename": "nlp_reference.txt",
            "detected_language": "en",
            "raw_text": ref_text,
        }
    ]

    # Test 1: English Paraphrase (Positive: similarity should be >= 0.82)
    sub_en_doc_id = str(uuid.uuid4())
    sub_en_text = (
        "Modern deep learning architectures transformed natural language processing "
        "by utilizing attention layers and self-supervised training strategies."
    )
    findings_en = matcher.match_documents(
        submission_document_id=sub_en_doc_id,
        submission_text=sub_en_text,
        submission_lang="en",
        candidate_docs=candidate_docs,
    )
    assert len(findings_en) >= 1
    assert findings_en[0].category == "paraphrase"
    assert findings_en[0].semantic_similarity >= settings.SEMANTIC_PARAPHRASE_THRESHOLD

    # Test 2: Hindi Translation (Positive: similarity should be >= 0.80)
    sub_hi_doc_id = str(uuid.uuid4())
    sub_hi_text = (
        "गहरे तंत्रिका नेटवर्क ने ट्रांसफार्मर ध्यान तंत्र और स्व-पर्यवेक्षित "
        "प्रशिक्षण के माध्यम से प्राकृतिक भाषा समझ में क्रांति ला दी है।"
    )
    findings_hi = matcher.match_documents(
        submission_document_id=sub_hi_doc_id,
        submission_text=sub_hi_text,
        submission_lang="hi",
        candidate_docs=candidate_docs,
    )
    assert len(findings_hi) >= 1
    assert findings_hi[0].category == "potential_translation"
    assert findings_hi[0].semantic_similarity >= settings.SEMANTIC_TRANSLATION_THRESHOLD
    assert findings_hi[0].language_pair == "hi-en"

    # Test 3: Hard Negative (Completely unrelated domain: baking bread)
    sub_neg_doc_id = str(uuid.uuid4())
    sub_neg_text = (
        "Baking artisanal sourdough bread requires precise water temperature, "
        "fresh yeast culture, whole grain flour, and long overnight fermentation."
    )
    findings_neg = matcher.match_documents(
        submission_document_id=sub_neg_doc_id,
        submission_text=sub_neg_text,
        submission_lang="en",
        candidate_docs=candidate_docs,
    )
    assert len(findings_neg) == 0, "Hard negative must be rejected by calibrated threshold"

    # Clean up
    _delete_test_doc(db_repo, ref_doc_id)


def test_hybrid_analysis_modes_and_union_coverage(provider):
    """
    Tests HybridAnalysisService across lexical, semantic, and hybrid modes.
    Verifies that hybrid mode computes non-overlapping union coverage.
    """
    db_repo = get_local_repo()
    service = get_hybrid_service()

    # Create reference document
    ref_id = str(uuid.uuid4())
    ref_text = (
        "Photosynthesis in green plants converts light energy into chemical energy "
        "stored in carbohydrate molecules such as glucose. Chlorophyll absorbs solar radiation."
    )
    _insert_test_doc(
        db_repo,
        doc_id=ref_id,
        filename="bio_ref.txt",
        text=ref_text,
        lang="en",
    )

    # Submission with both verbatim copy and paraphrased text
    sub_id = str(uuid.uuid4())
    sub_text = (
        "Photosynthesis in green plants converts light energy into chemical energy "
        "stored in carbohydrate molecules such as glucose. "
        "Plant chloroplasts harness the power of sunlight to generate vital organic sugars."
    )
    _insert_test_doc(
        db_repo,
        doc_id=sub_id,
        filename="bio_sub.txt",
        text=sub_text,
        lang="en",
    )

    user_id = "00000000-0000-0000-0000-000000000001"

    # 1. Test Mode: Lexical
    lex_id = str(uuid.uuid4())
    db_repo.create_analysis(
        analysis_id=lex_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        reference_document_id=ref_id,
        detection_mode="lexical",
    )
    res_lex = service.run_analysis(
        analysis_id=lex_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        detection_mode="lexical",
        reference_document_id=ref_id,
    )
    assert res_lex["detection_mode"] == "lexical"
    assert res_lex["overall_lexical_coverage_percent"] > 0
    assert res_lex["overall_semantic_coverage_percent"] == 0.0

    # 2. Test Mode: Semantic
    sem_id = str(uuid.uuid4())
    db_repo.create_analysis(
        analysis_id=sem_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        reference_document_id=ref_id,
        detection_mode="semantic",
    )
    res_sem = service.run_analysis(
        analysis_id=sem_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        detection_mode="semantic",
        reference_document_id=ref_id,
    )
    assert res_sem["detection_mode"] == "semantic"
    assert res_sem["overall_semantic_coverage_percent"] > 0
    assert res_sem["overall_lexical_coverage_percent"] == 0.0

    # 3. Test Mode: Hybrid
    hyb_id = str(uuid.uuid4())
    db_repo.create_analysis(
        analysis_id=hyb_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        reference_document_id=ref_id,
        detection_mode="hybrid",
    )
    res_hyb = service.run_analysis(
        analysis_id=hyb_id,
        owner_user_id=user_id,
        submission_document_id=sub_id,
        mode="direct",
        detection_mode="hybrid",
        reference_document_id=ref_id,
    )
    assert res_hyb["detection_mode"] == "hybrid"
    assert res_hyb["overall_lexical_coverage_percent"] > 0
    assert res_hyb["overall_semantic_coverage_percent"] > 0
    assert res_hyb["hybrid_evidence_coverage_percent"] >= res_hyb["overall_lexical_coverage_percent"]
    assert res_hyb["net_adjusted_score_percent"] > 0

    # Clean up
    _delete_test_doc(db_repo, ref_id)
    _delete_test_doc(db_repo, sub_id)


def test_api_analyses_models_info(client):
    """Verifies GET /api/v1/analyses/models/info endpoint returns active model metadata."""
    resp = client.get("/api/v1/analyses/models/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "multilingual-e5-small" in data["model_name"]
    assert data["embedding_dimension"] == 384
    assert data["max_sequence_length"] == 512
    assert "paraphrase_threshold" in data
    assert "translation_threshold" in data
    assert data["runtime_device"] in ("cpu", "cuda")


def test_api_create_analysis_with_detection_mode(client):
    """Verifies POST /api/v1/analyses accepts detection_mode and returns Phase 4 fields."""
    # Create ref doc
    ref_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("api_ref.txt", b"Renewable solar and wind energy are critical components of global sustainability initiatives.")},
        data={"title": "Clean Energy Reference"},
    )
    assert ref_resp.status_code == 201
    ref_id = ref_resp.json()["document_id"]

    # Create sub doc (paraphrase)
    sub_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("api_sub.txt", b"Sustainable green power like wind and solar panels play vital roles in worldwide ecological efforts.")},
        data={"title": "Clean Energy Submission"},
    )
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["document_id"]

    # Run hybrid analysis
    analysis_resp = client.post(
        "/api/v1/analyses?sync_processing=true",
        json={
            "submission_document_id": sub_id,
            "reference_document_id": ref_id,
            "mode": "direct",
            "detection_mode": "hybrid",
        },
    )
    assert analysis_resp.status_code == 202
    an_data = analysis_resp.json()
    an_id = an_data["analysis_id"]

    # Get results
    get_resp = client.get(f"/api/v1/analyses/{an_id}")
    assert get_resp.status_code == 200
    res = get_resp.json()

    assert res["status"] == "completed"
    assert res["detection_mode"] == "hybrid"
    assert "overall_lexical_coverage_percent" in res
    assert "overall_semantic_coverage_percent" in res
    assert "hybrid_evidence_coverage_percent" in res
    assert "net_adjusted_score_percent" in res
    assert res["model_metadata"] is not None
    assert "multilingual-e5-small" in res["model_metadata"]["model_name"]

    # Clean up
    client.delete(f"/api/v1/documents/{ref_id}")
    client.delete(f"/api/v1/documents/{sub_id}")
