"""
SQLAlchemy ORM Models implementing Phase 0 Data Model
Adheres to docs/03-data/data-model.md
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from plagiarism.db.base import Base

# Robust pgvector type fallback
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType
    class Vector(UserDefinedType):
        def __init__(self, dim: int = 768):
            self.dim = dim
        def get_col_spec(self, **kw) -> str:
            return f"vector({self.dim})"


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="STUDENT")
    full_name = Column(String(255), nullable=True)
    institution_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="owner", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_public_within_tenant = Column(Boolean, default=False, nullable=False)
    document_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    owner = relationship("User", back_populates="collections")
    permissions = relationship("CollectionPermission", back_populates="collection", cascade="all, delete-orphan")


class CollectionPermission(Base):
    __tablename__ = "collection_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission_level = Column(String(16), nullable=False, default="READ")
    granted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    collection = relationship("Collection", back_populates="permissions")
    __table_args__ = (UniqueConstraint("collection_id", "user_id", name="uq_collection_user"),)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(128), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    char_count = Column(Integer, default=0, nullable=False)
    raw_text = Column(Text, nullable=False)
    detected_language = Column(String(8), nullable=True)
    status = Column(String(32), default="READY", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    owner = relationship("User", back_populates="documents")
    passages = relationship("Passage", back_populates="document", cascade="all, delete-orphan")
    source_meta = relationship("DocumentSource", back_populates="document", uselist=False, cascade="all, delete-orphan")


class CollectionDocument(Base):
    __tablename__ = "collection_documents"

    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    indexed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(String(32), default="INDEXED", nullable=False)


class DocumentSource(Base):
    __tablename__ = "document_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    publication_year = Column(Integer, nullable=True)
    license = Column(String(64), default="CC-BY-4.0", nullable=False)
    provenance_uri = Column(String(1024), nullable=True)

    document = relationship("Document", back_populates="source_meta")


class Passage(Base):
    __tablename__ = "passages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    language = Column(String(8), default="en", nullable=False)

    document = relationship("Document", back_populates="passages")
    fingerprints = relationship("Fingerprint", back_populates="passage", cascade="all, delete-orphan")
    embedding = relationship("Embedding", back_populates="passage", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_offset > start_offset", name="check_passage_offsets_valid"),
    )


class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    hash_value = Column(BigInteger, nullable=False, index=True)
    passage_id = Column(UUID(as_uuid=True), ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)

    passage = relationship("Passage", back_populates="fingerprints")


class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    id = Column(String(64), primary_key=True)
    model_identifier = Column(String(128), nullable=False)
    model_revision = Column(String(64), nullable=False)
    dimensions = Column(Integer, default=768, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    passage_id = Column(UUID(as_uuid=True), ForeignKey("passages.id", ondelete="CASCADE"), unique=True, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    model_config_id = Column(String(64), ForeignKey("model_configurations.id"), nullable=False)
    embedding = Column(Vector(768), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    passage = relationship("Passage", back_populates="embedding")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    submission_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(16), nullable=False)
    target_collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True)
    eligible_code_points = Column(Integer, default=0, nullable=False)
    overall_lexical_coverage_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    overall_semantic_coverage_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    net_adjusted_score_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    report_path = Column(String(512), nullable=True)
    status = Column(String(32), default="queued", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="analyses")
    findings = relationship("Finding", back_populates="analysis", cascade="all, delete-orphan")
    job = relationship("AnalysisJob", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String(16), nullable=False, default="queued")
    progress_percent = Column(Integer, default=0, nullable=False)
    current_step = Column(String(64), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    analysis = relationship("Analysis", back_populates="job")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    reference_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(32), nullable=False)
    confidence = Column(String(16), nullable=False)
    submission_start_offset = Column(Integer, nullable=False)
    submission_end_offset = Column(Integer, nullable=False)
    submission_excerpt = Column(Text, nullable=False)
    reference_start_offset = Column(Integer, nullable=False)
    reference_end_offset = Column(Integer, nullable=False)
    reference_excerpt = Column(Text, nullable=False)
    reference_page_number = Column(Integer, default=1, nullable=False)
    lexical_similarity = Column(Numeric(5, 4), default=0.0000, nullable=False)
    semantic_similarity = Column(Numeric(5, 4), default=0.0000, nullable=False)
    is_quoted = Column(Boolean, default=False, nullable=False)
    is_in_bibliography = Column(Boolean, default=False, nullable=False)
    is_excluded = Column(Boolean, default=False, nullable=False)

    analysis = relationship("Analysis", back_populates="findings")


class Exclusion(Base):
    __tablename__ = "exclusions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(String(32), nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    review_label = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    details = Column(JSONB, nullable=True)


class DeletionLedger(Base):
    """Durable append-only deletion tombstone ledger for anti-resurrection DR reconciliation."""
    __tablename__ = "deletion_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    requested_by = Column(UUID(as_uuid=True), nullable=True)
    requested_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSONB, nullable=True)
