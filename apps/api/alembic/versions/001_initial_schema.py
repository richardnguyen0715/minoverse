"""Initial schema — Phase 0 foundation tables.

Revision ID: 001
Creates: vault_files, resources, resource_contents, resource_chunks,
         chunk_embeddings (pgvector), notes, wiki_links, tags, resource_tags,
         ingestion_jobs.

Revises: None
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all Phase 0 foundation tables."""
    # Enable pgvector extension — required before creating VECTOR columns.
    # This is idempotent.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # vault_files — filesystem index
    op.create_table(
        "vault_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("relative_path", sa.Text, unique=True, nullable=False),
        sa.Column("absolute_path", sa.Text, nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("file_size", sa.BigInteger),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_modified_at", sa.DateTime(timezone=True)),
    )

    # resources — universal knowledge object
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vault_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vault_files.id", ondelete="SET NULL")),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("canonical_title", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("canonical_url", sa.Text),
        sa.Column("source_platform", sa.String(100)),
        sa.Column("author", sa.Text),
        sa.Column("language", sa.String(10)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("saved_at", sa.DateTime(timezone=True)),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("semantic_hash", sa.String(64)),
        sa.Column("importance_score", sa.Float),
        sa.Column("quality_score", sa.Float),
        sa.Column("relevance_score", sa.Float),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_resources_resource_type", "resources", ["resource_type"])
    op.create_index("ix_resources_is_archived", "resources", ["is_archived"])
    op.create_index(
        "ix_resources_metadata_gin", "resources", ["metadata"],
        postgresql_using="gin",
    )

    # resource_contents — normalized parsed content
    op.create_table(
        "resource_contents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_type", sa.Text),
        sa.Column("raw_markdown", sa.Text),
        sa.Column("clean_text", sa.Text),
        sa.Column("html_content", sa.Text),
        sa.Column("transcript_content", sa.Text),
        sa.Column("token_count", sa.Integer),
        sa.Column("char_count", sa.Integer),
        sa.Column("reading_time_minutes", sa.Integer),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("parsed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # resource_chunks — chunking layer for RAG
    op.create_table(
        "resource_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("semantic_label", sa.Text),
        sa.Column("token_count", sa.Integer),
        sa.Column("start_offset", sa.Integer),
        sa.Column("end_offset", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resource_chunks_resource_id", "resource_chunks", ["resource_id"])

    # chunk_embeddings — pgvector semantic layer
    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resource_chunks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", sa.Text, nullable=False),  # Placeholder; real migration uses VECTOR(1536)
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Real vector column: ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(1536)
    # Done after pgvector extension is confirmed:
    op.execute("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")
    op.execute(
        "CREATE INDEX chunk_embedding_idx ON chunk_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # notes — Obsidian-native note system
    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vault_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vault_files.id", ondelete="SET NULL")),
        sa.Column("title", sa.Text),
        sa.Column("note_type", sa.String(50)),
        sa.Column("frontmatter", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # wiki_links — Obsidian wiki-link graph
    op.create_table(
        "wiki_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notes.id", ondelete="SET NULL")),
        sa.Column("anchor_text", sa.Text),
        sa.Column("resolved_resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wiki_links_source_note_id", "wiki_links", ["source_note_id"])
    op.create_index("ix_wiki_links_target_note_id", "wiki_links", ["target_note_id"])

    # tags — hierarchical tagging
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, unique=True, nullable=False),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("parent_tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="SET NULL")),
    )

    # resource_tags — hybrid manual + AI tagging
    op.create_table(
        "resource_tags",
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("generated_by_ai", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ingestion_jobs — async ingestion pipeline
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("raw_payload", postgresql.JSONB),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])


def downgrade() -> None:
    """Drop all Phase 0 foundation tables."""
    op.drop_table("ingestion_jobs")
    op.drop_table("resource_tags")
    op.drop_table("tags")
    op.drop_table("wiki_links")
    op.drop_table("notes")
    op.drop_table("chunk_embeddings")
    op.drop_table("resource_chunks")
    op.drop_table("resource_contents")
    op.drop_table("resources")
    op.drop_table("vault_files")
