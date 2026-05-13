"""Event type definitions for the minoverse event bus.

All events in the system are typed using this enum.
Publishers and subscribers must agree on event types.
"""
from enum import StrEnum


class EventType(StrEnum):
    """Canonical event types for the minoverse event bus.

    Events flow through Redis pub/sub channels.
    Each event type maps to a dedicated channel: f"minoverse:{event_type}".
    """

    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    NOTE_UPDATED = "note_updated"
    EMBEDDING_COMPLETED = "embedding_completed"
    SUMMARY_COMPLETED = "summary_completed"
