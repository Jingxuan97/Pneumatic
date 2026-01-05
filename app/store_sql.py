# app/store_sql.py
from typing import Dict, Any, List, Optional
from sqlalchemy import select, insert, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models import User, Conversation, ConversationMember, Message
from datetime import datetime, timezone
import asyncio

class SQLStore:
    def __init__(self):
        pass

    # Users
    async def create_user(self, username: str, password_hash: str) -> Dict[str, str]:
        """Create a new user with username and password hash."""
        async with AsyncSessionLocal() as session:
            u = User(username=username, password_hash=password_hash)
            session.add(u)
            try:
                await session.commit()
                await session.refresh(u)
                return {"id": u.id, "username": u.username}
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Username '{username}' already exists")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            row = await session.get(User, user_id)
            if row:
                return {"id": row.id, "username": row.username}
            return None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username, including password hash for verification."""
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(User).where(User.username == username))
            row = q.scalar_one_or_none()
            if row:
                return {
                    "id": row.id,
                    "username": row.username,
                    "password_hash": row.password_hash
                }
            return None

    # Conversations
    async def create_conversation(self, title: str, member_ids: List[str]) -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            # validate members exist
            q = await session.execute(select(User.id).where(User.id.in_(member_ids)))
            present = {r[0] for r in q.all()}
            missing = [m for m in member_ids if m not in present]
            if missing:
                raise KeyError(f"users do not exist: {missing}")

            conv = Conversation(title=title)
            session.add(conv)
            # flush to get conv.id
            await session.flush()
            conv_id = conv.id
            # add members
            for uid in member_ids:
                cm = ConversationMember(conversation_id=conv_id, user_id=uid)
                session.add(cm)
            await session.commit()
            return {"id": conv_id, "title": title, "members": member_ids}

    async def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            conv = await session.get(Conversation, conv_id)
            if not conv:
                return None
            q = await session.execute(select(ConversationMember.user_id).where(ConversationMember.conversation_id == conv_id))
            members = [r[0] for r in q.all()]
            return {"id": conv.id, "title": conv.title, "members": members}

    # Messages
    async def save_message(self, message_payload) -> Dict[str, Any]:
        """
        message_payload expected to have attributes:
          - message_id, sender_id, conversation_id, content
        Raises KeyError if conversation missing, PermissionError if sender not member.
        """
        async with AsyncSessionLocal() as session:
            # validate conversation
            conv = await session.get(Conversation, message_payload.conversation_id)
            if not conv:
                raise KeyError("conversation does not exist")
            # validate sender membership
            q = await session.execute(select(ConversationMember).where(
                ConversationMember.conversation_id == message_payload.conversation_id,
                ConversationMember.user_id == message_payload.sender_id
            ))
            if not q.first():
                raise PermissionError("sender is not a member of this conversation")

            # Create message; rely on unique(message_id) to dedupe
            msg = Message(
                message_id=message_payload.message_id,
                sender_id=message_payload.sender_id,
                conversation_id=message_payload.conversation_id,
                content=message_payload.content,
                created_at=datetime.now(timezone.utc)
            )
            session.add(msg)
            try:
                await session.commit()
                await session.refresh(msg)
            except IntegrityError as e:
                await session.rollback()
                # likely duplicate message_id — return existing message
                existing = await session.execute(select(Message).where(Message.message_id == message_payload.message_id))
                row = existing.scalar_one_or_none()
                if row:
                    return {
                        "id": row.id,
                        "message_id": row.message_id,
                        "sender_id": row.sender_id,
                        "conversation_id": row.conversation_id,
                        "content": row.content,
                        "created_at": row.created_at.isoformat() + "Z"
                    }
                # else rethrow
                raise
            return {
                "id": msg.id,
                "message_id": msg.message_id,
                "sender_id": msg.sender_id,
                "conversation_id": msg.conversation_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() + "Z"
            }

    async def list_messages(self, conv_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            q = await session.execute(
                select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at.asc()).limit(limit)
            )
            rows = q.scalars().all()
            return [
                {
                    "id": r.id,
                    "message_id": r.message_id,
                    "sender_id": r.sender_id,
                    "conversation_id": r.conversation_id,
                    "content": r.content,
                    "created_at": r.created_at.isoformat() + "Z"
                } for r in rows
            ]

# create a single module-level store instance
store = SQLStore()
