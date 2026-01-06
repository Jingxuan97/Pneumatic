# app/main.py
import os
import logging
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from .routes import router
from .auth_routes import router as auth_router
from .websockets import manager
from .store_sql import store  # async SQL store
from .schemas import MessageCreate
from .db import DATABASE_URL, init_db, engine
from .auth import get_current_user_websocket
from .metrics import metrics
from .logging_config import setup_logging
from .tracing import setup_tracing
from .rate_limit import RateLimitMiddleware, RateLimiter

# Setup structured JSON logging
setup_logging()
logger = logging.getLogger("pneumatic")

app = FastAPI(title="Pneumatic Chat - Secure")

# Setup OpenTelemetry tracing (must be before other middleware)
setup_tracing(app, engine)
logger.info("OpenTelemetry tracing initialized", extra={"extra_fields": {"event": "tracing_init"}})

# Setup rate limiting
rate_limiter = RateLimiter(
    requests_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60")),
    requests_per_hour=int(os.environ.get("RATE_LIMIT_PER_HOUR", "1000"))
)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Configure CORS
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns 200 if the service is running.
    """
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 if the service is ready to accept traffic.
    Used by load balancers to determine if the instance can handle requests.
    """
    try:
        # Check database connectivity
        # Simple check: try to query the database
        from sqlalchemy import text
        from .db import engine
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return Response(
            content='{"status": "not ready", "error": "database unavailable"}',
            status_code=503,
            media_type="application/json"
        )


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    metrics_text = metrics.get_metrics_prometheus(manager)
    return Response(content=metrics_text, media_type="text/plain")


@app.on_event("startup")
async def on_startup():
    logger.info("Starting Pneumatic Chat application", extra={"extra_fields": {"event": "startup"}})
    # Ensure database tables exist (creates if missing, preserves existing data)
    await init_db()
    logger.info("Database initialized", extra={"extra_fields": {"event": "db_init"}})



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
        metrics.increment_websocket_connection()
        logger.info(
            "WebSocket connection established",
            extra={"extra_fields": {"user_id": user_id, "event": "websocket_connect"}}
        )

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
                    # Track message metric
                    metrics.increment_message_sent()
                    logger.info(
                        "Message sent via WebSocket",
                        extra={"extra_fields": {
                            "user_id": user_id,
                            "conversation_id": saved["conversation_id"],
                            "message_id": saved["message_id"],
                            "event": "message_sent"
                        }}
                    )
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
