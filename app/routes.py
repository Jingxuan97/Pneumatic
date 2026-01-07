# app/routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from .schemas import ConversationCreate, MessageCreate
from .store_sql import store
import asyncio
from .websockets import manager
from .auth import get_current_user
from .metrics import metrics

router = APIRouter()

@router.get("/users")
async def list_users(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all registered users (excluding the current user).
    Requires authentication.
    """
    users = await store.list_all_users(exclude_user_id=current_user["id"])
    return {"users": users}

@router.get("/conversations")
async def list_conversations(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all conversations for the current user.
    Requires authentication.
    """
    conversations = await store.list_user_conversations(current_user["id"])
    return {"conversations": conversations}

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    c: ConversationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new conversation.
    Requires authentication. The current user is automatically added as a member.

    For 1-on-1 conversations (exactly 2 members), this will return an existing
    conversation if one already exists between these two users.
    """
    # Ensure current user is included in members
    member_ids = list(set(c.member_ids + [current_user["id"]]))

    # Check if this is a 1-on-1 conversation (exactly 2 members)
    if len(member_ids) == 2:
        # Check if a 1-on-1 conversation already exists
        existing_conv = await store.find_one_on_one_conversation(
            member_ids[0],
            member_ids[1]
        )
        if existing_conv:
            # Return existing conversation instead of creating a duplicate
            return existing_conv

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
    # Track message metric
    metrics.increment_message_sent()
    return saved
