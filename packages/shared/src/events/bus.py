"""Redis pub/sub event bus for minoverse.

Provides publish() and subscribe() for the shared event bus.
All inter-service communication goes through this module.

Constraints:
    - Publishers must not embed business logic.
    - Subscribers process one event type per handler.
    - Each event is published as JSON on channel f"minoverse:{event_type}".
"""
import json
from collections.abc import AsyncGenerator
from typing import TypeVar

import redis.asyncio as aioredis
import structlog

from .payloads import EventPayload
from .types import EventType

logger = structlog.get_logger(__name__)

_CHANNEL_PREFIX = "minoverse"

PayloadT = TypeVar("PayloadT", bound=EventPayload)


def _build_channel_name(event_type: EventType) -> str:
    """Build the Redis channel name for an event type."""
    return f"{_CHANNEL_PREFIX}:{event_type}"


async def publish_event(
    redis_client: aioredis.Redis,
    event_type: EventType,
    payload: EventPayload,
) -> None:
    """Publish an event to the Redis pub/sub bus.

    Args:
        redis_client: Active async Redis client.
        event_type: The type of event to publish.
        payload: Pydantic payload model for the event.

    Raises:
        EventPublishError: If the Redis publish call fails.

    Side Effects:
        - Publishes a JSON message to the Redis channel.
    """
    channel = _build_channel_name(event_type)
    message = payload.model_dump_json()

    try:
        subscriber_count = await redis_client.publish(channel, message)
        logger.info(
            "event_published",
            event_type=event_type,
            channel=channel,
            subscriber_count=subscriber_count,
            event_id=str(payload.event_id),
        )
    except Exception as exc:
        logger.error(
            "event_publish_failed",
            event_type=event_type,
            channel=channel,
            error=str(exc),
        )
        raise


async def subscribe_to_event(
    redis_client: aioredis.Redis,
    event_type: EventType,
) -> AsyncGenerator[dict, None]:
    """Subscribe to an event type and yield raw message dicts.

    Args:
        redis_client: Active async Redis client.
        event_type: The event type channel to subscribe to.

    Yields:
        dict: Deserialized JSON message payload.
    """
    channel = _build_channel_name(event_type)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    logger.info("event_subscribed", event_type=event_type, channel=channel)

    async for message in pubsub.listen():
        if message["type"] == "message":
            raw_data: str = message["data"]
            yield json.loads(raw_data)
