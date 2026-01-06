# app/websockets.py
import asyncio
from typing import Dict, List, Union, Optional
from fastapi import WebSocket, status, WebSocketDisconnect
from .store_sql import store
from .schemas import MessageCreate
from .pubsub import pubsub, presence

import logging
logger = logging.getLogger("pneumatic")
logger.setLevel(logging.DEBUG)
# ensure handler exists once
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)


class ConnectionManager:
    def __init__(self):
        # Store multiple connections per user as a list
        self.active: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()
        # Track which conversations each user has joined (for Redis subscription)
        self.user_conversations: Dict[str, set] = {}  # user_id -> set of conversation_ids

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            if user_id not in self.active:
                self.active[user_id] = []
                self.user_conversations[user_id] = set()
            self.active[user_id].append(websocket)
            logger.debug("User %s connected. Total connections: %d", user_id, len(self.active[user_id]))

        # Set presence in Redis
        if presence:
            await presence.set_presence(user_id)

    async def disconnect(self, user_id: str, websocket: WebSocket = None):
        async with self.lock:
            if user_id not in self.active:
                return

            if websocket is None:
                # Remove all connections for this user (backward compatibility)
                connections = self.active.pop(user_id, [])
                for ws in connections:
                    try:
                        await ws.close()
                    except Exception:
                        pass
            else:
                # Remove specific websocket connection
                if websocket in self.active[user_id]:
                    self.active[user_id].remove(websocket)
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                # Clean up empty lists
                if not self.active[user_id]:
                    del self.active[user_id]
                    self.user_conversations.pop(user_id, None)
                logger.debug("User %s disconnected. Remaining connections: %d", user_id, len(self.active.get(user_id, [])))

        # Remove presence if user has no more connections
        if presence and user_id not in self.active:
            await presence.remove_presence(user_id)

    async def send_personal(self, user_id: str, data: dict):
        """Send data to all connections for a specific user"""
        async with self.lock:
            connections = self.active.get(user_id, [])

        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                logger.exception("failed to send to user %s", user_id)

    async def broadcast_to_conversation(self, conv_id: str, data: dict):
        """
        Publish message to Redis channel instead of directly broadcasting.
        Redis pub/sub will handle distribution across all nodes.

        Args:
            conv_id: Conversation ID
            data: Message data to broadcast
        """
        logger.debug("broadcast_to_conversation called for conv=%s", conv_id)

        if not pubsub or not pubsub._connected:
            logger.warning("Redis pub/sub not available, falling back to local broadcast")
            await self._local_broadcast(conv_id, data)
            return

        try:
            # Publish to Redis channel
            channel = pubsub.get_channel_name(conv_id)
            await pubsub.publish(channel, data)
            logger.debug("Published message to Redis channel %s", channel)
        except Exception as e:
            logger.exception("Failed to publish to Redis, falling back to local: %s", e)
            await self._local_broadcast(conv_id, data)

    async def _local_broadcast(self, conv_id: str, data: dict):
        """
        Fallback local broadcast (original implementation).
        Used when Redis is not available.
        """
        try:
            conv = await store.get_conversation(conv_id)
        except Exception:
            logger.exception("failed to load conversation %s", conv_id)
            return

        if not conv:
            logger.debug("no conversation found for id=%s", conv_id)
            return

        member_ids = conv.get("members") or []
        logger.debug("conversation %s members=%r", conv_id, member_ids)

        # For each member, send to all their active websocket connections
        async with self.lock:
            # Create a snapshot of connections to avoid holding lock during sends
            member_connections = {
                member_id: list(self.active.get(member_id, []))
                for member_id in member_ids
            }

        for member_id, ws_list in member_connections.items():
            if not ws_list:
                logger.debug("no active connection for member %s", member_id)
                continue

            for ws in ws_list:
                try:
                    logger.debug("sending payload to member=%s websocket=%s", member_id, getattr(ws, "__repr__", lambda: ws)())
                    await ws.send_json(data)
                except Exception:
                    logger.exception("failed to send to member %s", member_id)

    async def join_conversation(self, user_id: str, conv_id: str):
        """
        Subscribe to a conversation channel in Redis.
        This ensures the node receives messages for this conversation.
        """
        if not pubsub or not pubsub._connected:
            logger.debug("Redis not available, skipping subscription")
            return

        async with self.lock:
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = set()

            if conv_id in self.user_conversations[user_id]:
                # Already subscribed
                return

            self.user_conversations[user_id].add(conv_id)

        # Subscribe to Redis channel
        channel = pubsub.get_channel_name(conv_id)
        await pubsub.subscribe(channel, self._handle_redis_message)
        logger.debug("User %s joined conversation %s (subscribed to channel %s)", user_id, conv_id, channel)

    async def _handle_redis_message(self, channel: str, data: dict):
        """
        Handle message received from Redis pub/sub.
        Forward to local WebSocket connections.
        """
        # Extract conversation ID from channel name (format: "conv:conversation_id")
        if not channel.startswith("conv:"):
            logger.warning("Received message on unexpected channel: %s", channel)
            return

        conv_id = channel[5:]  # Remove "conv:" prefix

        # Get conversation members
        try:
            conv = await store.get_conversation(conv_id)
            if not conv:
                logger.debug("Conversation %s not found", conv_id)
                return

            member_ids = conv.get("members") or []
        except Exception:
            logger.exception("Failed to load conversation %s", conv_id)
            return

        # Forward to local connections
        async with self.lock:
            member_connections = {
                member_id: list(self.active.get(member_id, []))
                for member_id in member_ids
            }

        for member_id, ws_list in member_connections.items():
            if not ws_list:
                continue

            for ws in ws_list:
                try:
                    await ws.send_json(data)
                    logger.debug("Forwarded Redis message to user %s", member_id)
                except Exception:
                    logger.exception("Failed to forward message to user %s", member_id)

manager = ConnectionManager()