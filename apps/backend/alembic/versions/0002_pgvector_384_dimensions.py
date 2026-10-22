"""Schema update for 384-dimensional multilingual-e5-small embeddings and passage_embeddings index

Revision ID: 0002_pgvector_384_dimensions
Revises: 0001_initial_schema
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_pgvector_384_dimensions'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update model_configurations seed for multilingual-e5-small (384 dimensions)
    op.execute("""
        INSERT INTO model_configurations (id, model_identifier, model_revision, dimensions, is_active)
        VALUES ('multilingual-e5-small-v1', 'intfloat/multilingual-e5-small', '614241f622f53c4eeff9890bdc4f31cfecc418b3', 384, true)
        ON CONFLICT (id) DO NOTHING;
    """)

    # 2. Create or adapt passage_embeddings table matching VectorIndex repository
    op.execute("""
        CREATE TABLE IF NOT EXISTS passage_embeddings (
            passage_id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(64) NOT NULL,
            sequence_index INTEGER NOT NULL,
            start_offset INTEGER NOT NULL,
            end_offset INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            model_id VARCHAR(128) NOT NULL,
            model_revision VARCHAR(64) NOT NULL,
            embedding vector(384) NOT NULL,
            text_hash VARCHAR(64) NOT NULL,
            created_at VARCHAR(64) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_passage_emb_doc ON passage_embeddings(document_id);
        CREATE INDEX IF NOT EXISTS idx_passage_emb_hash ON passage_embeddings(text_hash);
    """)

    # Try creating HNSW index for cosine distance if supported by pgvector version
    try:
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_passage_emb_cosine_hnsw 
            ON passage_embeddings USING hnsw (embedding vector_cosine_ops);
        """)
    except Exception:
        # Fallback to IVFFlat if HNSW is not supported
        try:
            op.execute("""
                CREATE INDEX IF NOT EXISTS idx_passage_emb_cosine_ivf 
                ON passage_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """)
        except Exception:
            pass


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS passage_embeddings CASCADE;")
