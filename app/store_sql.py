# app/store_sql.py
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func
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
    async def create_user(self, username: str, password_hash: str, full_name: Optional[str] = None) -> Dict[str, str]:
        """Create a new user with username, password hash, and optional full name."""
        async with AsyncSessionLocal() as session:
            u = User(username=username, password_hash=password_hash, full_name=full_name)
            session.add(u)
            try:
                await session.commit()
                await session.refresh(u)
                return {"id": u.id, "username": u.username, "full_name": u.full_name}
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Username '{username}' already exists")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            row = await session.get(User, user_id)
            if row:
                return {"id": row.id, "username": row.username, "full_name": row.full_name}
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
                    "full_name": row.full_name,
                    "password_hash": row.password_hash
                }
            return None

    async def list_all_users(self, exclude_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all users, optionally excluding a specific user."""
        async with AsyncSessionLocal() as session:
            query = select(User)
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            q = await session.execute(query.order_by(User.username))
            rows = q.scalars().all()
            return [
                {
                    "id": row.id,
                    "username": row.username,
                    "full_name": row.full_name
                }
                for row in rows
            ]

    async def find_one_on_one_conversation(self, user1_id: str, user2_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing 1-on-1 conversation between two users.
        Returns None if no such conversation exists.
        """
        async with AsyncSessionLocal() as session:
            # Find conversations where both users are members
            # This query finds conversations that have exactly these two members

            # Get all conversations where user1 is a member
            q1 = await session.execute(
                select(ConversationMember.conversation_id)
                .where(ConversationMember.user_id == user1_id)
            )
            user1_conv_ids = {r[0] for r in q1.all()}

            if not user1_conv_ids:
                return None

            # Get conversations where user2 is also a member
            q2 = await session.execute(
                select(ConversationMember.conversation_id)
                .where(
                    ConversationMember.conversation_id.in_(user1_conv_ids),
                    ConversationMember.user_id == user2_id
                )
            )
            shared_conv_ids = {r[0] for r in q2.all()}

            if not shared_conv_ids:
                return None

            # Check if any of these conversations have exactly 2 members (1-on-1)
            for conv_id in shared_conv_ids:
                q_members = await session.execute(
                    select(func.count(ConversationMember.user_id))
                    .where(ConversationMember.conversation_id == conv_id)
                )
                member_count = q_members.scalar()

                if member_count == 2:
                    # Found a 1-on-1 conversation
                    conv = await session.get(Conversation, conv_id)
                    if conv:
                        members = [user1_id, user2_id]
                        return {"id": conv.id, "title": conv.title, "members": members}

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

    async def list_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        async with AsyncSessionLocal() as session:
            # Get all conversation IDs where user is a member
            q = await session.execute(
                select(ConversationMember.conversation_id)
                .where(ConversationMember.user_id == user_id)
            )
            conv_ids = [r[0] for r in q.all()]

            if not conv_ids:
                return []

            # Get conversation details
            q = await session.execute(
                select(Conversation).where(Conversation.id.in_(conv_ids))
            )
            conversations = q.scalars().all()

            # Get members for each conversation
            result = []
            for conv in conversations:
                q_members = await session.execute(
                    select(ConversationMember.user_id)
                    .where(ConversationMember.conversation_id == conv.id)
                )
                members = [r[0] for r in q_members.all()]
                result.append({
                    "id": conv.id,
                    "title": conv.title,
                    "members": members
                })

            return result

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
            # Convert timezone-aware datetime to naive for database compatibility
            # The column is defined as timezone=False, so we need naive datetime
            now_utc = datetime.now(timezone.utc)
            created_at_naive = now_utc.replace(tzinfo=None) if now_utc.tzinfo else now_utc

            msg = Message(
                message_id=message_payload.message_id,
                sender_id=message_payload.sender_id,
                conversation_id=message_payload.conversation_id,
                content=message_payload.content,
                created_at=created_at_naive
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
