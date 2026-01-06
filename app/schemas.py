# app/schemas.py
from typing import List, Any, Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    full_name: str | None = None
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str | None = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

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