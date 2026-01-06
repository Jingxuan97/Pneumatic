# app/pubsub.py
"""
Redis Pub/Sub adapter for broadcasting messages across multiple nodes.
Handles publishing messages to Redis channels and subscribing to receive messages.
"""
import os
import json
import asyncio
import logging
from typing import Optional, Callable, Awaitable, List
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

logger = logging.getLogger("pneumatic")


class RedisPubSub:
    """
    Redis Pub/Sub wrapper for message broadcasting across multiple nodes.

    Each node subscribes to conversation channels and forwards messages
    to local WebSocket connections.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis connection.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379/0)
        """
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.subscribed_channels: set = set()
        self.message_handler: Optional[Callable[[str, dict], Awaitable[None]]] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._connected = False

    async def connect(self):
        """Connect to Redis and initialize pub/sub."""
        try:
            self.redis = Redis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            # Test connection
            await self.redis.ping()
            self._connected = True
            logger.info("Connected to Redis at %s", self.redis_url)
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            raise

    async def disconnect(self):
        """Disconnect from Redis and cleanup."""
        self._connected = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.aclose()
            self.pubsub = None

        if self.redis:
            await self.redis.aclose()
            self.redis = None

        logger.info("Disconnected from Redis")

    async def publish(self, channel: str, message: dict):
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name (e.g., "conv:conversation_id")
            message: Message dict to publish
        """
        if not self._connected or not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            message_str = json.dumps(message)
            await self.redis.publish(channel, message_str)
            logger.debug("Published message to channel %s", channel)
        except Exception as e:
            logger.exception("Failed to publish message to channel %s: %s", channel, e)
            raise

    async def subscribe(self, channel: str, handler: Callable[[str, dict], Awaitable[None]]):
        """
        Subscribe to a Redis channel and set up message handler.

        Args:
            channel: Channel name to subscribe to
            handler: Async function that receives (channel, message_dict)
        """
        if not self._connected or not self.pubsub:
            raise RuntimeError("Redis not connected")

        if channel in self.subscribed_channels:
            logger.debug("Already subscribed to channel %s", channel)
            return

        try:
            await self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
            self.message_handler = handler

            # Start listener task if not already running
            if not self._listener_task or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._listen())

            logger.debug("Subscribed to channel %s", channel)
        except Exception as e:
            logger.exception("Failed to subscribe to channel %s: %s", channel, e)
            raise

    async def unsubscribe(self, channel: str):
        """Unsubscribe from a Redis channel."""
        if not self._connected or not self.pubsub:
            return

        if channel not in self.subscribed_channels:
            return

        try:
            await self.pubsub.unsubscribe(channel)
            self.subscribed_channels.discard(channel)
            logger.debug("Unsubscribed from channel %s", channel)
        except Exception as e:
            logger.exception("Failed to unsubscribe from channel %s: %s", channel, e)

    async def _listen(self):
        """Listen for messages from subscribed channels."""
        logger.info("Starting Redis pub/sub listener")

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data_str = message["data"]

                    try:
                        data = json.loads(data_str)
                        if self.message_handler:
                            await self.message_handler(channel, data)
                    except json.JSONDecodeError:
                        logger.error("Failed to decode message from channel %s", channel)
                    except Exception as e:
                        logger.exception("Error handling message from channel %s: %s", channel, e)
        except asyncio.CancelledError:
            logger.info("Redis pub/sub listener cancelled")
        except Exception as e:
            logger.exception("Error in Redis pub/sub listener: %s", e)

    def get_channel_name(self, conversation_id: str) -> str:
        """Get Redis channel name for a conversation."""
        return f"conv:{conversation_id}"


class PresenceManager:
    """
    Manages user presence using Redis keys with TTL.
    Tracks which users are online and when they were last seen.
    """

    def __init__(self, redis: Redis):
        """
        Initialize presence manager.

        Args:
            redis: Redis client instance
        """
        self.redis = redis
        self.presence_ttl = int(os.environ.get("PRESENCE_TTL_SECONDS", "300"))  # 5 minutes default
        self.presence_key_prefix = "presence:"

    async def set_presence(self, user_id: str, metadata: Optional[dict] = None):
        """
        Set user as online with optional metadata.

        Args:
            user_id: User ID
            metadata: Optional dict with additional info (e.g., {"last_seen": timestamp})
        """
        key = f"{self.presence_key_prefix}{user_id}"
        value = json.dumps(metadata or {})
        await self.redis.setex(key, self.presence_ttl, value)
        logger.debug("Set presence for user %s", user_id)

    async def remove_presence(self, user_id: str):
        """Remove user presence (user went offline)."""
        key = f"{self.presence_key_prefix}{user_id}"
        await self.redis.delete(key)
        logger.debug("Removed presence for user %s", user_id)

    async def is_online(self, user_id: str) -> bool:
        """Check if user is online."""
        key = f"{self.presence_key_prefix}{user_id}"
        exists = await self.redis.exists(key)
        return bool(exists)

    async def get_online_users(self, user_ids: List[str]) -> List[str]:
        """
        Get list of online users from a list of user IDs.

        Args:
            user_ids: List of user IDs to check

        Returns:
            List of user IDs that are online
        """
        if not user_ids:
            return []

        keys = [f"{self.presence_key_prefix}{uid}" for uid in user_ids]
        # Use pipeline for efficiency
        pipe = self.redis.pipeline()
        for key in keys:
            pipe.exists(key)
        results = await pipe.execute()

        online = [uid for uid, exists in zip(user_ids, results) if exists]
        return online

    async def refresh_presence(self, user_id: str):
        """Refresh presence TTL (user is still active)."""
        key = f"{self.presence_key_prefix}{user_id}"
        await self.redis.expire(key, self.presence_ttl)
        logger.debug("Refreshed presence for user %s", user_id)


# Global instances (will be initialized in main.py)
pubsub: Optional[RedisPubSub] = None
presence: Optional[PresenceManager] = None
