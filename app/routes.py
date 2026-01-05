# app/routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from .schemas import ConversationCreate, MessageCreate
from .store_sql import store
import asyncio
from .websockets import manager
from .auth import get_current_user

router = APIRouter()

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    c: ConversationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new conversation.
    Requires authentication. The current user is automatically added as a member.
    """
    # Ensure current user is included in members
    member_ids = list(set(c.member_ids + [current_user["id"]]))

    try:
        conv = await store.create_conversation(c.title, member_ids)
        return conv
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/conversations/{conv_id}/messages")
async def get_messages(
    conv_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get messages from a conversation.
    Requires authentication and membership in the conversation.
    """
    # Verify user is a member of the conversation
    conv = await store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="conversation not found")

    if current_user["id"] not in conv["members"]:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this conversation"
        )

    try:
        msgs = await store.list_messages(conv_id, limit=limit)
        return {"messages": msgs}
    except KeyError:
        raise HTTPException(status_code=404, detail="conversation not found")

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def post_message(
    m: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message to a conversation.
    Requires authentication. The sender_id must match the authenticated user.
    """
    # Enforce that sender_id matches authenticated user
    if m.sender_id != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="sender_id must match authenticated user"
        )

    try:
        saved = await store.save_message(m)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    payload = {"type": "message", "message": saved}
    asyncio.create_task(manager.broadcast_to_conversation(m.conversation_id, payload))
    return saved
