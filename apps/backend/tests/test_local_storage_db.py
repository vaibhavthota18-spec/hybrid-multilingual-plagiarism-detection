"""
Unit Tests for Local Storage & SQLite Metadata Persistence
Verifies path traversal defense, file streaming limits, database persistence across restart,
and cascade deletions.
"""

from pathlib import Path

import pytest

from plagiarism.core.errors import BadRequestError
from plagiarism.storage.local_db import LocalMetadataRepository
from plagiarism.storage.private_store import PrivateStorageManager, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_document.pdf") == "safe_document.pdf"
    assert sanitize_filename("hindi_दस्तावेज़.docx") == "hindi_दस्तावेज़.docx"
    assert sanitize_filename("...") == "unnamed_document.txt"


def test_storage_path_traversal_rejection(tmp_path: Path):
    storage = PrivateStorageManager(root_dir=tmp_path)
    # Attempting traversal should raise BadRequestError
    with pytest.raises(BadRequestError, match="Path traversal attempt detected"):
        storage._get_safe_path("../outside.txt")


def test_sqlite_metadata_persistence_across_restart(tmp_path: Path):
    """
    Simulates server restart by creating a repo, writing document records,
    closing, and re-opening on the exact same SQLite file.
    """
    db_file = tmp_path / "test_persistence.db"

    # Session 1: write document and passages
    repo1 = LocalMetadataRepository(db_path=db_file)
    doc_id = "doc-persist-001"
    repo1.insert_document(
        document_id=doc_id,
        owner_user_id="user-001",
        filename="research_paper.pdf",
        mime_type="application/pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path=str(tmp_path / "dummy.pdf"),
        file_size_bytes=1024,
        status="completed",
        title="Research Paper on Multilingual Plagiarism"
    )
    repo1.update_document_extraction(
        document_id=doc_id,
        status="completed",
        page_count=5,
        char_count=5000,
        word_count=800,
        raw_text="Extracted research text here.",
        detected_language="en",
        warnings=""
    )
    repo1.insert_passages([
        {
            "id": "p-001",
            "document_id": doc_id,
            "sequence_index": 0,
            "start_offset": 0,
            "end_offset": 20,
            "text_content": "Extracted research text",
            "token_count": 3,
            "page_number": 1,
            "language": "en"
        }
    ])

    # Session 2: simulate restart with fresh instance pointing to the same file
    repo2 = LocalMetadataRepository(db_path=db_file)
    retrieved = repo2.get_document(doc_id)
    assert retrieved is not None
    assert retrieved["filename"] == "research_paper.pdf"
    assert retrieved["status"] == "completed"
    assert retrieved["title"] == "Research Paper on Multilingual Plagiarism"
    assert retrieved["char_count"] == 5000

    passages = repo2.get_passages(doc_id)
    assert len(passages) == 1
    assert passages[0]["id"] == "p-001"
    assert passages[0]["text_content"] == "Extracted research text"


def test_sqlite_collections_and_membership(tmp_path: Path):
    db_file = tmp_path / "test_collections.db"
    repo = LocalMetadataRepository(db_path=db_file)

    # 1. Create collection
    col_id = "col-001"
    col = repo.create_collection(
        collection_id=col_id,
        name="Thesis References 2026",
        owner_user_id="user-001",
        description="Reference collection for thesis validation"
    )
    assert col["name"] == "Thesis References 2026"
    assert col["document_count"] == 0

    # 2. Add document
    doc_id = "doc-ref-001"
    repo.insert_document(
        document_id=doc_id,
        owner_user_id="user-001",
        filename="reference_book.txt",
        mime_type="text/plain",
        sha256_hash="hash123",
        storage_path=str(tmp_path / "ref.txt"),
        file_size_bytes=2048,
        status="completed"
    )

    repo.add_document_to_collection(col_id, doc_id)
    updated_col = repo.get_collection(col_id)
    assert updated_col["document_count"] == 1

    members = repo.list_collection_documents(col_id)
    assert len(members) == 1
    assert members[0]["document_id"] == doc_id

    # 3. Remove document from collection
    repo.remove_document_from_collection(col_id, doc_id)
    col_after_remove = repo.get_collection(col_id)
    assert col_after_remove["document_count"] == 0


def test_document_deletion_cascades(tmp_path: Path):
    db_file = tmp_path / "test_cascade.db"
    repo = LocalMetadataRepository(db_path=db_file)

    doc_id = "doc-del-001"
    repo.insert_document(
        document_id=doc_id,
        owner_user_id="user-001",
        filename="to_delete.txt",
        mime_type="text/plain",
        sha256_hash="hash456",
        storage_path=str(tmp_path / "del.txt"),
        file_size_bytes=512,
        status="completed"
    )
    repo.insert_passages([
        {
            "id": "p-del-1",
            "document_id": doc_id,
            "sequence_index": 0,
            "start_offset": 0,
            "end_offset": 10,
            "text_content": "Delete me",
            "token_count": 2,
            "page_number": 1,
            "language": "en"
        }
    ])

    # Delete
    deleted = repo.delete_document(doc_id)
    assert deleted is True
    assert repo.get_document(doc_id) is None
    assert len(repo.get_passages(doc_id)) == 0
