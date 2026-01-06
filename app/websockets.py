# app/websockets.py
import asyncio
from typing import Dict, List, Union, Optional
from fastapi import WebSocket, status, WebSocketDisconnect
from .store_sql import store
from .schemas import MessageCreate

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

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            if user_id not in self.active:
                self.active[user_id] = []
            self.active[user_id].append(websocket)
            logger.debug("User %s connected. Total connections: %d", user_id, len(self.active[user_id]))

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
                logger.debug("User %s disconnected. Remaining connections: %d", user_id, len(self.active.get(user_id, [])))

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
        Broadcast message to all members of a conversation.

        Args:
            conv_id: Conversation ID
            data: Message data to broadcast
        """
        logger.debug("broadcast_to_conversation called for conv=%s", conv_id)
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
                    logger.debug("sending payload to member=%s", member_id)
                    await ws.send_json(data)
                except Exception:
                    logger.exception("failed to send to member %s", member_id)

manager = ConnectionManager()