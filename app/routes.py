# app/routes.py
from fastapi import APIRouter, HTTPException, status
from .schemas import UserCreate, ConversationCreate, MessageCreate
from .store import store
import asyncio
from .websockets import manager

router = APIRouter()

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(u: UserCreate):
    user = store.create_user(u.username)
    return user

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(c: ConversationCreate):
    try:
        conv = store.create_conversation(c.title, c.member_ids)
        return conv
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str, limit: int = 50):
    try:
        msgs = store.list_messages(conv_id, limit=limit)
        return {"messages": msgs}
    except KeyError:
        raise HTTPException(status_code=404, detail="conversation not found")

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def post_message(m: MessageCreate):
    try:
        saved = store.save_message(m)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    payload = {"type": "message", "message": saved}
    # We're inside an async function now so create_task will find a running loop.
    asyncio.create_task(manager.broadcast_to_conversation(m.conversation_id, payload))
    return saved