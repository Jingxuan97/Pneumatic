# app/main.py
import os
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routes import router
from .auth_routes import router as auth_router
from .websockets import manager
from .store_sql import store  # async SQL store
from .schemas import MessageCreate
from .db import DATABASE_URL, init_db
from .auth import get_current_user_websocket

app = FastAPI(title="Pneumatic Chat - Secure")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers including Authorization
)

app.include_router(auth_router)
app.include_router(router)


@app.on_event("startup")
async def on_startup():
    # Ensure database tables exist (creates if missing, preserves existing data)
    await init_db()



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Secure WebSocket endpoint for real-time messaging.
    Requires authentication token in query parameter or Authorization header.
    Token format: ?token=<access_token> or Authorization: Bearer <access_token>
    """
    try:
        # Authenticate user from token
        user = await get_current_user_websocket(websocket)
        user_id = user["id"]

        await manager.connect(user_id, websocket)

        try:
            while True:
                data = await websocket.receive_json()
                if not isinstance(data, dict):
                    continue
                typ = data.get("type")
                if typ == "join":
                    conv_id = data.get("conversation_id")
                    if not conv_id:
                        await websocket.send_json({"type": "error", "reason": "conversation_id required"})
                        continue

                    # Verify user is a member of the conversation
                    conv = await store.get_conversation(conv_id)
                    if not conv:
                        await websocket.send_json({"type": "error", "reason": "conversation not found"})
                        continue

                    if user_id not in conv["members"]:
                        await websocket.send_json({"type": "error", "reason": "not a member of this conversation"})
                        continue

                    await websocket.send_json({"type": "joined", "conversation_id": conv_id})

                elif typ == "message":
                    # validate message shape
                    try:
                        mc = MessageCreate(
                            message_id=data["message_id"],
                            sender_id=user_id,  # Enforce authenticated user as sender
                            conversation_id=data["conversation_id"],
                            content=data["content"],
                        )
                    except KeyError:
                        await websocket.send_json({"type": "error", "reason": "invalid message shape"})
                        continue

                    # save_message is async now — await it
                    try:
                        saved = await store.save_message(mc)
                    except (KeyError, PermissionError) as e:
                        await websocket.send_json({"type": "error", "reason": str(e)})
                        continue

                    payload = {"type": "message", "message": saved}
                    # broadcast to members (manager.broadcast_to_conversation is async)
                    await manager.broadcast_to_conversation(saved["conversation_id"], payload)
                else:
                    await websocket.send_json({"type": "error", "reason": "unknown type"})
        except WebSocketDisconnect:
            # client disconnected; ensure we remove the connection and exit cleanly
            await manager.disconnect(user_id, websocket)
            return
        except Exception as e:
            # ensure we remove the connection on any other error
            await manager.disconnect(user_id, websocket)
            raise
    except WebSocketException as e:
        # Authentication failed
        try:
            await websocket.close(code=e.code, reason=e.reason)
        except Exception:
            pass
        return
    except Exception as e:
        # Other errors during connection
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
        return
