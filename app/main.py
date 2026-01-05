# app/main.py
import os
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect
from .routes import router
from .websockets import manager
from .store_sql import store  # async SQL store
from .schemas import MessageCreate
from .db import DATABASE_URL, reset_db

app = FastAPI(title="Minimal Chat - Modular (SQL)")

app.include_router(router)


@app.on_event("startup")
async def on_startup():
    # For local dev using the default sqlite dev DB, reset schema to ensure tests run
    # against a clean database. Do NOT do this in production.
    dev_sqlite = DATABASE_URL.startswith("sqlite") and ("./dev.db" in DATABASE_URL or ":memory:" in DATABASE_URL)
    if dev_sqlite:
        # careful: this will DROP all tables in the dev DB
        await reset_db()


import logging
logger = logging.getLogger("pneumatic")
logger.setLevel(logging.DEBUG)
# ensure handler exists once
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)



@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    logger.debug("WS connect start user_id=%s", user_id)

    # now store.get_user is async — await it
    user = await store.get_user(user_id)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue
            typ = data.get("type")
            if typ == "join":
                await websocket.send_json({"type": "joined", "conversation_id": data.get("conversation_id")})
                logger.debug("WS %s received join for conv=%s", user_id, data.get("conversation_id"))

            elif typ == "message":
                # validate message shape
                try:
                    mc = MessageCreate(
                        message_id=data["message_id"],
                        sender_id=user_id,
                        conversation_id=data["conversation_id"],
                        content=data["content"],
                    )
                except KeyError:
                    await websocket.send_json({"type": "error", "reason": "invalid message shape"})
                    continue

                logger.debug("WS %s saving message id=%s conv=%s", user_id, data["message_id"], data["conversation_id"])
                # save_message is async now — await it
                try:
                    saved = await store.save_message(mc)
                except (KeyError, PermissionError) as e:
                    await websocket.send_json({"type": "error", "reason": str(e)})
                    continue
                logger.debug("WS %s saved message -> %r", user_id, saved)

                payload = {"type": "message", "message": saved}
                # broadcast to members (manager.broadcast_to_conversation is async)
                logger.debug("WS %s calling manager.broadcast_to_conversation conv=%s", user_id, saved["conversation_id"])
                await manager.broadcast_to_conversation(saved["conversation_id"], payload)
            else:
                await websocket.send_json({"type": "error", "reason": "unknown type"})
    except WebSocketDisconnect:
        # client disconnected; ensure we remove the connection and exit cleanly
        await manager.disconnect(user_id)
        return
    except Exception:
        # ensure we remove the connection on any other error
        await manager.disconnect(user_id)
        raise
