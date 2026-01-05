# app/websockets.py
import asyncio
from typing import Dict
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
        self.active: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active[user_id] = websocket

    async def disconnect(self, user_id: str):
        async with self.lock:
            ws = self.active.pop(user_id, None)
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass

    async def send_personal(self, user_id: str, data: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(data)

    async def broadcast_to_conversation(self, conv_id: str, data: dict):
        """
        Send `data` (a JSON-serialisable dict) to every websocket
        for each member in the conversation.

        - conv is loaded from async store
        - supports self.active[user_id] being either a websocket or a list of websockets
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

        # For each member, send to all their active websocket(s)
        for member_id in member_ids:
            conns = self.active.get(member_id)
            if not conns:
                logger.debug("no active connection for member %s", member_id)
                continue

            # normalize to list
            ws_list = conns if isinstance(conns, list) else [conns]
            for ws in ws_list:
                try:
                    logger.debug("sending payload to member=%s websocket=%s", member_id, getattr(ws, "__repr__", lambda: ws)())
                    await ws.send_json(data)
                except Exception:
                    logger.exception("failed to send to member %s", member_id)

manager = ConnectionManager()