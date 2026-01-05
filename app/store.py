# app/store.py
import uuid
from datetime import datetime
from typing import Dict, List, Any, Set
from .schemas import MessageCreate

class InMemoryStore:
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
        self.seen_message_ids: Set[str] = set()

    def create_user(self, username: str) -> Dict[str, str]:
        user_id = str(uuid.uuid4())
        self.users[user_id] = {"id": user_id, "username": username}
        return self.users[user_id]

    def get_user(self, user_id: str):
        return self.users.get(user_id)

    def create_conversation(self, title: str, member_ids: List[str]) -> Dict[str, Any]:
        for mid in member_ids:
            if mid not in self.users:
                raise KeyError(f"user {mid} does not exist")
        conv_id = str(uuid.uuid4())
        conv = {"id": conv_id, "title": title, "members": member_ids}
        self.conversations[conv_id] = conv
        self.messages[conv_id] = []
        return conv

    def get_conversation(self, conv_id: str):
        return self.conversations.get(conv_id)

    def save_message(self, message_payload: MessageCreate) -> Dict[str, Any]:
        if message_payload.message_id in self.seen_message_ids:
            for m in self.messages.get(message_payload.conversation_id, []):
                if m["message_id"] == message_payload.message_id:
                    return m
        if message_payload.conversation_id not in self.conversations:
            raise KeyError("conversation does not exist")
        conv = self.conversations[message_payload.conversation_id]
        if message_payload.sender_id not in conv["members"]:
            raise PermissionError("sender is not a member of this conversation")
        now = datetime.utcnow().isoformat() + "Z"
        msg = {
            "id": str(uuid.uuid4()),
            "message_id": message_payload.message_id,
            "sender_id": message_payload.sender_id,
            "conversation_id": message_payload.conversation_id,
            "content": message_payload.content,
            "created_at": now,
        }
        self.messages[message_payload.conversation_id].append(msg)
        self.seen_message_ids.add(message_payload.message_id)
        return msg

    def list_messages(self, conv_id: str, limit: int = 50):
        if conv_id not in self.messages:
            raise KeyError("conversation does not exist")
        return self.messages[conv_id][-limit:]

store = InMemoryStore()