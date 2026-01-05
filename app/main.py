# app/main.py
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect
from .routes import router
from .websockets import manager
from .store import store
from .schemas import MessageCreate

app = FastAPI(title="Minimal Chat - Modular")

app.include_router(router)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    if not store.get_user(user_id):
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
            elif typ == "message":
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
                try:
                    saved = store.save_message(mc)
                except (KeyError, PermissionError) as e:
                    await websocket.send_json({"type": "error", "reason": str(e)})
                    continue
                payload = {"type": "message", "message": saved}
                await manager.broadcast_to_conversation(saved["conversation_id"], payload)
            else:
                await websocket.send_json({"type": "error", "reason": "unknown type"})
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception:
        await manager.disconnect(user_id)
        raise