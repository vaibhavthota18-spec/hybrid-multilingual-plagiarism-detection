"""Initial schema migration with pgvector extension and core entities

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Users Table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(32), nullable=False, server_default='STUDENT'),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # 3. Collections Table
    op.create_table(
        'collections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_public_within_tenant', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('document_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. Collection Permissions
    op.create_table(
        'collection_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('collections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_level', sa.String(16), server_default='READ', nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('collection_id', 'user_id', name='uq_collection_user')
    )

    # 5. Documents Table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('page_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('char_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('detected_language', sa.String(8), nullable=True),
        sa.Column('status', sa.String(32), server_default='READY', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_documents_owner', 'documents', ['owner_user_id'])
    op.create_index('idx_documents_sha256', 'documents', ['sha256_hash'])

    # 6. Collection Documents
    op.create_table(
        'collection_documents',
        sa.Column('collection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('collections.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('indexed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(32), server_default='INDEXED', nullable=False),
    )

    # 7. Document Sources
    op.create_table(
        'document_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('license', sa.String(64), server_default='CC-BY-4.0', nullable=False),
        sa.Column('provenance_uri', sa.String(1024), nullable=True),
    )

    # 8. Passages Table
    op.create_table(
        'passages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_index', sa.Integer(), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('language', sa.String(8), server_default='en', nullable=False),
        sa.CheckConstraint('end_offset > start_offset', name='check_passage_offsets_valid')
    )
    op.create_index('idx_passages_doc_seq', 'passages', ['document_id', 'sequence_index'])

    # 9. Fingerprints Table
    op.create_table(
        'fingerprints',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('hash_value', sa.BigInteger(), nullable=False),
        sa.Column('passage_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('passages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
    )
    op.create_index('idx_fingerprints_hash', 'fingerprints', ['hash_value'])
    op.create_index('idx_fingerprints_doc', 'fingerprints', ['document_id'])

    # 10. Model Configurations
    op.create_table(
        'model_configurations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('model_identifier', sa.String(128), nullable=False),
        sa.Column('model_revision', sa.String(64), nullable=False),
        sa.Column('dimensions', sa.Integer(), server_default='768', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Seed baseline model
    op.execute("""
        INSERT INTO model_configurations (id, model_identifier, model_revision, dimensions, is_active)
        VALUES ('multilingual-e5-base-v1', 'intfloat/multilingual-e5-base', '1c1070ff081498e82ff0543e2a22026197fa11c5', 768, true)
        ON CONFLICT (id) DO NOTHING;
    """)

    # 11. Embeddings Table (with pgvector type)
    op.execute("""
        CREATE TABLE embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            passage_id UUID UNIQUE NOT NULL REFERENCES passages(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            model_config_id VARCHAR(64) NOT NULL REFERENCES model_configurations(id),
            embedding vector(768) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX idx_embeddings_doc ON embeddings(document_id);")

    # 12. Analyses Table
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mode', sa.String(16), nullable=False),
        sa.Column('target_collection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('collections.id'), nullable=True),
        sa.Column('eligible_code_points', sa.Integer(), server_default='0', nullable=False),
        sa.Column('overall_lexical_coverage_percent', sa.Numeric(5, 2), server_default='0.00', nullable=False),
        sa.Column('overall_semantic_coverage_percent', sa.Numeric(5, 2), server_default='0.00', nullable=False),
        sa.Column('net_adjusted_score_percent', sa.Numeric(5, 2), server_default='0.00', nullable=False),
        sa.Column('report_path', sa.String(512), nullable=True),
        sa.Column('status', sa.String(32), server_default='queued', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 13. Analysis Jobs Table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analyses.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('status', sa.String(16), server_default='queued', nullable=False),
        sa.Column('progress_percent', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_step', sa.String(64), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 14. Findings Table
    op.create_table(
        'findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reference_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('confidence', sa.String(16), nullable=False),
        sa.Column('submission_start_offset', sa.Integer(), nullable=False),
        sa.Column('submission_end_offset', sa.Integer(), nullable=False),
        sa.Column('submission_excerpt', sa.Text(), nullable=False),
        sa.Column('reference_start_offset', sa.Integer(), nullable=False),
        sa.Column('reference_end_offset', sa.Integer(), nullable=False),
        sa.Column('reference_excerpt', sa.Text(), nullable=False),
        sa.Column('reference_page_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('lexical_similarity', sa.Numeric(5, 4), server_default='0.0000', nullable=False),
        sa.Column('semantic_similarity', sa.Numeric(5, 4), server_default='0.0000', nullable=False),
        sa.Column('is_quoted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_in_bibliography', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_excluded', sa.Boolean(), server_default='false', nullable=False),
    )
    op.create_index('idx_findings_analysis', 'findings', ['analysis_id'])

    # 15. Exclusions Table
    op.create_table(
        'exclusions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(32), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
    )

    # 16. Reviews Table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('findings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('review_label', sa.String(32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 17. Audit Events Table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(64), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
    )

    # 18. Deletion Ledger Table (Independent DR Anti-Resurrection Ledger)
    op.create_table(
        'deletion_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(32), server_default='PENDING', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
    )
    op.create_index('idx_deletion_ledger_doc', 'deletion_ledger', ['document_id'])


def downgrade() -> None:
    op.drop_table('deletion_ledger')
    op.drop_table('audit_events')
    op.drop_table('reviews')
    op.drop_table('exclusions')
    op.drop_table('findings')
    op.drop_table('analysis_jobs')
    op.drop_table('analyses')
    op.drop_table('embeddings')
    op.drop_table('model_configurations')
    op.drop_table('fingerprints')
    op.drop_table('passages')
    op.drop_table('document_sources')
    op.drop_table('collection_documents')
    op.drop_table('documents')
    op.drop_table('collection_permissions')
    op.drop_table('collections')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS vector;")
