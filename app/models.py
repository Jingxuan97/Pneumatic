# app/models.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime, timezone

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.String(length=36), primary_key=True, default=gen_uuid)
    username = sa.Column(sa.String(length=150), nullable=False, unique=True)
    full_name = sa.Column(sa.String(length=255), nullable=True)
    password_hash = sa.Column(sa.String(length=255), nullable=False)

class Conversation(Base):
    __tablename__ = "conversations"
    id = sa.Column(sa.String(length=36), primary_key=True, default=gen_uuid)
    title = sa.Column(sa.String(length=255), nullable=True)

class ConversationMember(Base):
    __tablename__ = "conversation_members"
    conversation_id = sa.Column(sa.String(length=36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id = sa.Column(sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

class Message(Base):
    __tablename__ = "messages"
    id = sa.Column(sa.String(length=36), primary_key=True, default=gen_uuid)
    message_id = sa.Column(sa.String(length=255), nullable=False, unique=True, index=True)  # client-supplied UUID for idempotency
    sender_id = sa.Column(sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = sa.Column(sa.String(length=36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    content = sa.Column(sa.Text(), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=False), nullable=False, default=utc_now, index=True)
