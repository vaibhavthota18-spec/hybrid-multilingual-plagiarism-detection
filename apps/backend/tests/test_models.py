"""
Unit Tests for Database Models and Schema Integrity
Verifies SQLAlchemy metadata matches Phase 0 Data Architecture
"""

import pytest
from sqlalchemy import inspect
from plagiarism.db.base import Base
from plagiarism.db.models import (
    User,
    Collection,
    CollectionPermission,
    Document,
    CollectionDocument,
    DocumentSource,
    Passage,
    Fingerprint,
    ModelConfiguration,
    Embedding,
    Analysis,
    AnalysisJob,
    Finding,
    Exclusion,
    Review,
    AuditEvent,
    DeletionLedger,
)

EXPECTED_TABLES = {
    "users",
    "collections",
    "collection_permissions",
    "documents",
    "collection_documents",
    "document_sources",
    "passages",
    "fingerprints",
    "model_configurations",
    "embeddings",
    "analyses",
    "analysis_jobs",
    "findings",
    "exclusions",
    "reviews",
    "audit_events",
    "deletion_ledger",
}


def test_table_registration_completeness():
    """Verify all 17 required Phase 0 entity tables are declared in the Base metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    missing_tables = EXPECTED_TABLES - registered_tables
    assert not missing_tables, f"Missing registered tables in SQLAlchemy metadata: {missing_tables}"


def test_primary_keys_defined():
    """Verify each registered table defines a primary key."""
    for table_name, table in Base.metadata.tables.items():
        pks = [c.name for c in table.primary_key.columns]
        assert len(pks) > 0, f"Table {table_name} is missing a defined primary key"


def test_foreign_key_relationships():
    """Verify critical foreign key constraints across relational entities."""
    passages_table = Base.metadata.tables["passages"]
    fk_targets = {fk.column.table.name for fk in passages_table.foreign_keys}
    assert "documents" in fk_targets, "passages table must have a foreign key pointing to documents"

    embeddings_table = Base.metadata.tables["embeddings"]
    fk_targets = {fk.column.table.name for fk in embeddings_table.foreign_keys}
    assert "passages" in fk_targets, "embeddings table must reference passages"
    assert "model_configurations" in fk_targets, "embeddings table must reference model_configurations"

    findings_table = Base.metadata.tables["findings"]
    fk_targets = {fk.column.table.name for fk in findings_table.foreign_keys}
    assert "analyses" in fk_targets, "findings table must reference analyses"


def test_vector_column_definition():
    """Verify embeddings table defines a vector column with dimension 768 for Multilingual E5."""
    embeddings_table = Base.metadata.tables["embeddings"]
    assert "embedding" in embeddings_table.c, "embeddings table must contain an 'embedding' column"
    vector_col = embeddings_table.c["embedding"]
    # pgvector Vector type exposes dim attribute
    assert hasattr(vector_col.type, "dim"), "vector column must be a pgvector Vector type"
    assert vector_col.type.dim == 768, f"Expected vector dimension 768, got {vector_col.type.dim}"


def test_fingerprint_indexes():
    """Verify fingerprints table indexes hash_value for fast Winnowing candidate retrieval."""
    fp_table = Base.metadata.tables["fingerprints"]
    index_names = {idx.name for idx in fp_table.indexes}
    assert "ix_fingerprints_hash_value" in index_names or any("hash_value" in [c.name for c in idx.columns] for idx in fp_table.indexes), \
        "fingerprints table must have an index over hash_value"
