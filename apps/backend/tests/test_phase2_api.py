"""
Integration Tests for Phase 2 API Endpoints
Verifies /documents, /collections, and /comparisons/validate HTTP contracts and error envelopes.
"""

import pytest
from fastapi.testclient import TestClient

from plagiarism.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_upload_txt_document_success(client):
    """Verify multipart upload of a valid TXT document."""
    file_content = (
        b"Multilingual Ingestion Pipeline\n\n"
        b"Hindi: \xe0\xa4\xb8\xe0\xa4\xbe\xe0\xa4\xb9\xe0\xa4\xbf\xe0\xa4\xa4\xe0\xa5\x8d\xe0\xa4\xaf\xe0\xa4\xbf\xe0\xa4\x95 \xe0\xa4\x9a\xe0\xa5\x8b\xe0\xa4\xb0\xe0\xa5\x80\n\n"
        b"Telugu: \xe0\xb0\xb8\xe0\xb0\xbe\xe0\xb0\xb9\xe0\xb0\xbf\xe0\xb0\xa4\xe0\xb1\x8d\xe0\xb0\xaf \xe0\xb0\x9a\xe0\xb1\x8c\xe0\xb0\xb0\xe0\xb1\x8d\xe0\xb0\xaf\xe0\xb0\x82"
    )
    files = {"file": ("research_paper.txt", file_content, "text/plain")}
    data = {"title": "Multilingual Sample Paper", "language_hint": "auto"}

    response = client.post("/api/v1/documents?sync_processing=true", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert "document_id" in res_data
    assert res_data["filename"] == "research_paper.txt"
    assert res_data["title"] == "Multilingual Sample Paper"
    assert res_data["status"] == "completed"
    assert res_data["char_count"] > 0
    assert res_data["word_count"] > 0

    doc_id = res_data["document_id"]

    # Verify text preview
    text_resp = client.get(f"/api/v1/documents/{doc_id}/text")
    assert text_resp.status_code == 200
    text_data = text_resp.json()
    assert "Multilingual Ingestion Pipeline" in text_data["raw_text"]
    assert "साहित्यिक चोरी" in text_data["raw_text"]

    # Verify passages preview
    passages_resp = client.get(f"/api/v1/documents/{doc_id}/passages")
    assert passages_resp.status_code == 200
    passages_data = passages_resp.json()
    assert passages_data["total_passages"] >= 1
    assert len(passages_data["passages"]) >= 1


def test_upload_unsupported_extension_rejection(client):
    """Verify files with unsupported extensions are rejected with HTTP 415."""
    files = {"file": ("malicious.exe", b"MZbinarycontent", "application/x-dosexec")}
    response = client.post("/api/v1/documents", files=files)
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_upload_empty_file_rejection(client):
    """Verify empty 0-byte file upload is rejected with HTTP 400."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    response = client.post("/api/v1/documents", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "EMPTY_FILE"


def test_list_and_get_documents(client):
    """Verify paginated listing and single document metadata retrieval."""
    # List documents
    list_resp = client.get("/api/v1/documents?limit=10&offset=0")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert "items" in list_data
    assert "pagination" in list_data
    assert isinstance(list_data["items"], list)

    if list_data["items"]:
        doc_id = list_data["items"][0]["document_id"]
        # Get by ID
        get_resp = client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 200
        doc = get_resp.json()
        assert doc["document_id"] == doc_id
        assert "filename" in doc


def test_collections_crud_and_membership(client):
    """Verify reference collection lifecycle: create, list, add doc, list docs, remove doc."""
    # 1. Create collection
    col_payload = {
        "name": "Literature Review 2026",
        "description": "Corpus of published papers on NLP",
        "is_public_within_tenant": False
    }
    col_resp = client.post("/api/v1/collections", json=col_payload)
    assert col_resp.status_code == 201
    col_data = col_resp.json()
    assert "collection_id" in col_data
    col_id = col_data["collection_id"]
    assert col_data["name"] == "Literature Review 2026"

    # 2. List collections
    list_resp = client.get("/api/v1/collections")
    assert list_resp.status_code == 200
    assert any(c["collection_id"] == col_id for c in list_resp.json()["items"])

    # 3. Upload a document to add to collection
    upload_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("ref1.txt", b"Reference paper content text.", "text/plain")}
    )
    doc_id = upload_resp.json()["document_id"]

    # 4. Add document to collection
    add_resp = client.post(
        f"/api/v1/collections/{col_id}/documents",
        json={"document_id": doc_id}
    )
    assert add_resp.status_code == 201

    # 5. List collection documents
    docs_resp = client.get(f"/api/v1/collections/{col_id}/documents")
    assert docs_resp.status_code == 200
    docs_data = docs_resp.json()
    assert docs_data["total_documents"] == 1
    assert docs_data["documents"][0]["document_id"] == doc_id

    # 6. Remove document from collection
    del_doc_resp = client.delete(f"/api/v1/collections/{col_id}/documents/{doc_id}")
    assert del_doc_resp.status_code == 204


def test_comparison_input_validation(client):
    """Verify comparison preparation across Direct, One-to-Many, and Corpus modes."""
    # Upload submission doc
    sub_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("submission.txt", b"Student submission document content for plagiarism verification.", "text/plain")}
    )
    sub_id = sub_resp.json()["document_id"]

    # Upload reference doc
    ref_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("reference.txt", b"Original source reference document text.", "text/plain")}
    )
    ref_id = ref_resp.json()["document_id"]

    # 1. Direct mode success
    direct_req = {
        "submission_document_id": sub_id,
        "mode": "direct",
        "reference_document_id": ref_id
    }
    val_resp = client.post("/api/v1/comparisons/validate", json=direct_req)
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["status"] == "ready"
    assert val_data["reference_count"] == 1
    assert "Similarity detection will be implemented in Phase 3" in val_data["message"]

    # 2. Self comparison rejection
    self_req = {
        "submission_document_id": sub_id,
        "mode": "direct",
        "reference_document_id": sub_id
    }
    self_resp = client.post("/api/v1/comparisons/validate", json=self_req)
    assert self_resp.status_code == 400
    assert self_resp.json()["error"]["code"] == "SELF_COMPARISON"

    # 3. One-to-Many mode success
    o2m_req = {
        "submission_document_id": sub_id,
        "mode": "one_to_many",
        "reference_document_ids": [ref_id]
    }
    o2m_resp = client.post("/api/v1/comparisons/validate", json=o2m_req)
    assert o2m_resp.status_code == 200
    assert o2m_resp.json()["reference_count"] == 1

    # 4. Empty collection rejection
    col_resp = client.post("/api/v1/collections", json={"name": "Empty Collection Test"})
    empty_col_id = col_resp.json()["collection_id"]

    corpus_req = {
        "submission_document_id": sub_id,
        "mode": "corpus",
        "collection_id": empty_col_id
    }
    corpus_resp = client.post("/api/v1/comparisons/validate", json=corpus_req)
    assert corpus_resp.status_code == 400
    assert corpus_resp.json()["error"]["code"] == "EMPTY_COLLECTION"


def test_delete_document_success(client):
    """Verify document deletion removes metadata and file."""
    upload_resp = client.post(
        "/api/v1/documents?sync_processing=true",
        files={"file": ("to_be_deleted.txt", b"Temporary text content.", "text/plain")}
    )
    doc_id = upload_resp.json()["document_id"]

    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 204

    # Verify 404 after deletion
    get_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert get_resp.status_code == 404
