# app/schemas.py
from typing import List, Any
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str

class ConversationCreate(BaseModel):
    title: str
    member_ids: List[str]

class MessageCreate(BaseModel):
    message_id: str
    sender_id: str
    conversation_id: str
    content: str

class Message(BaseModel):
    id: str
    message_id: str
    sender_id: str
    conversation_id: str
    content: str
    created_at: str