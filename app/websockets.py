# app/websockets.py
import asyncio
from typing import Dict, List, Union, Optional
from fastapi import WebSocket, status, WebSocketDisconnect
from .store_sql import store
from .schemas import MessageCreate


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

    async def send_personal(self, user_id: str, data: dict):
        """Send data to all connections for a specific user"""
        async with self.lock:
            connections = self.active.get(user_id, [])

        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    async def broadcast_to_conversation(self, conv_id: str, data: dict):
        """
        Broadcast message to all members of a conversation.

        Args:
            conv_id: Conversation ID
            data: Message data to broadcast
        """
        try:
            conv = await store.get_conversation(conv_id)
        except Exception:
            return

        if not conv:
            return

        member_ids = conv.get("members") or []

        # For each member, send to all their active websocket connections
        async with self.lock:
            # Create a snapshot of connections to avoid holding lock during sends
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
                except Exception:
                    pass

manager = ConnectionManager()