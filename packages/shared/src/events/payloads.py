"""Pydantic payload models for each event type.

Every event published on the bus must use one of these payload models.
This ensures all consumers can deserialize events without ambiguity.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    """Base payload for all minoverse events.

    Constraints:
        - event_id is generated at publish time.
        - occurred_at is always UTC.
    """

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceCreatedPayload(EventPayload):
    """Payload for RESOURCE_CREATED events.

    Emitted after a new resource is persisted to the database.
    Triggers downstream ingestion pipeline steps.
    """

    resource_id: uuid.UUID
    resource_type: str
    vault_file_path: str | None = None


class ResourceUpdatedPayload(EventPayload):
    """Payload for RESOURCE_UPDATED events.

    Emitted when a resource's content or metadata changes.
    Triggers re-chunking, re-embedding, and re-tagging.
    """

    resource_id: uuid.UUID
    changed_fields: list[str] = Field(default_factory=list)


class NoteUpdatedPayload(EventPayload):
    """Payload for NOTE_UPDATED events.

    Emitted when a vault note file changes on disk.
    Triggers wiki-link re-extraction and graph update.
    """

    note_id: uuid.UUID
    vault_file_path: str


class EmbeddingCompletedPayload(EventPayload):
    """Payload for EMBEDDING_COMPLETED events.

    Emitted when all chunks of a resource have been embedded.
    Triggers retrieval index refresh.
    """

    resource_id: uuid.UUID
    chunk_count: int
    embedding_model: str


class SummaryCompletedPayload(EventPayload):
    """Payload for SUMMARY_COMPLETED events.

    Emitted when AI summary generation for a resource completes.
    """

    resource_id: uuid.UUID
    artifact_id: uuid.UUID
    model_name: str
