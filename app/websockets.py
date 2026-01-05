# app/websockets.py
import asyncio
from typing import Dict
from fastapi import WebSocket, status, WebSocketDisconnect
from .store import store
from .schemas import MessageCreate

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
        conv = store.get_conversation(conv_id)
        if not conv:
            return
        member_ids = conv["members"]
        send_tasks = []
        for uid in member_ids:
            ws = self.active.get(uid)
            if ws:
                send_tasks.append(asyncio.create_task(ws.send_json(data)))
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)

manager = ConnectionManager()