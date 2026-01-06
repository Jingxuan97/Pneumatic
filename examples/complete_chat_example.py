#!/usr/bin/env python3
"""
Complete example demonstrating all features of the Pneumatic chat application.
This script shows how to use the API programmatically.
"""
import asyncio
import json
import uuid
import httpx
import websockets
from typing import Optional


class PneumaticClient:
    """Client for interacting with Pneumatic chat API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.client = httpx.AsyncClient()

    async def signup(self, username: str, password: str) -> dict:
        """Create a new user account."""
        response = await self.client.post(
            f"{self.base_url}/auth/signup",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()

    async def login(self, username: str, password: str) -> dict:
        """Login and get tokens."""
        response = await self.client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        # Get user info
        user_info = await self.get_current_user()
        self.user_id = user_info["id"]
        self.username = user_info["username"]

        return data

    async def get_current_user(self) -> dict:
        """Get current authenticated user."""
        if not self.access_token:
            raise ValueError("Not logged in")

        response = await self.client.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()

    async def refresh_tokens(self) -> dict:
        """Refresh access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token")

        response = await self.client.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return data

    async def create_conversation(self, title: str, member_ids: list = None) -> dict:
        """Create a new conversation."""
        if not self.access_token:
            raise ValueError("Not logged in")

        response = await self.client.post(
            f"{self.base_url}/conversations",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"title": title, "member_ids": member_ids or []}
        )
        response.raise_for_status()
        return response.json()

    async def list_conversations(self) -> list:
        """List all conversations for current user."""
        if not self.access_token:
            raise ValueError("Not logged in")

        response = await self.client.get(
            f"{self.base_url}/conversations",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()["conversations"]

    async def get_messages(self, conversation_id: str, limit: int = 50) -> list:
        """Get messages from a conversation."""
        if not self.access_token:
            raise ValueError("Not logged in")

        response = await self.client.get(
            f"{self.base_url}/conversations/{conversation_id}/messages?limit={limit}",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()["messages"]

    async def send_message_http(self, conversation_id: str, content: str) -> dict:
        """Send a message via HTTP API."""
        if not self.access_token:
            raise ValueError("Not logged in")

        response = await self.client.post(
            f"{self.base_url}/messages",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "message_id": str(uuid.uuid4()),
                "sender_id": self.user_id,
                "conversation_id": conversation_id,
                "content": content
            }
        )
        response.raise_for_status()
        return response.json()

    async def connect_websocket(self):
        """Connect to WebSocket and return connection."""
        if not self.access_token:
            raise ValueError("Not logged in")

        uri = f"{self.ws_url}/ws?token={self.access_token}"
        return await websockets.connect(uri)

    async def send_websocket_message(self, ws, conversation_id: str, content: str):
        """Send a message via WebSocket."""
        message = {
            "type": "message",
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "content": content
        }
        await ws.send(json.dumps(message))

    async def join_conversation(self, ws, conversation_id: str):
        """Join a conversation via WebSocket."""
        await ws.send(json.dumps({
            "type": "join",
            "conversation_id": conversation_id
        }))

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def example_basic_usage():
    """Example: Basic chat flow."""
    print("=" * 60)
    print("Example 1: Basic Chat Flow")
    print("=" * 60)

    # Create clients
    alice = PneumaticClient()
    bob = PneumaticClient()

    try:
        # Step 1: Sign up
        print("\n1. Creating users...")
        await alice.signup("alice_demo", "password123")
        await bob.signup("bob_demo", "password123")
        print("   ✅ Users created")

        # Step 2: Login
        print("\n2. Logging in...")
        await alice.login("alice_demo", "password123")
        await bob.login("bob_demo", "password123")
        print(f"   ✅ Alice logged in (ID: {alice.user_id})")
        print(f"   ✅ Bob logged in (ID: {bob.user_id})")

        # Step 3: Create conversation
        print("\n3. Creating conversation...")
        conv = await alice.create_conversation(
            "Alice & Bob Chat",
            member_ids=[bob.user_id]
        )
        conv_id = conv["id"]
        print(f"   ✅ Conversation created (ID: {conv_id})")

        # Step 4: Send message via HTTP
        print("\n4. Sending message via HTTP...")
        msg = await alice.send_message_http(conv_id, "Hello Bob!")
        print(f"   ✅ Message sent: {msg['content']}")

        # Step 5: Get messages
        print("\n5. Fetching messages...")
        messages = await bob.get_messages(conv_id)
        print(f"   ✅ Found {len(messages)} message(s)")
        for m in messages:
            print(f"      - {m['content']}")

    finally:
        await alice.close()
        await bob.close()


async def example_websocket_chat():
    """Example: Real-time WebSocket chat."""
    print("\n" + "=" * 60)
    print("Example 2: Real-Time WebSocket Chat")
    print("=" * 60)

    alice = PneumaticClient()
    bob = PneumaticClient()

    try:
        # Setup
        await alice.signup("alice_ws", "pass123")
        await bob.signup("bob_ws", "pass123")
        await alice.login("alice_ws", "pass123")
        await bob.login("bob_ws", "pass123")

        conv = await alice.create_conversation("WS Chat", [bob.user_id])
        conv_id = conv["id"]

        print(f"\n📝 Conversation: {conv_id}")
        print("🔌 Connecting WebSockets...")

        # Connect WebSockets
        ws_alice = await alice.connect_websocket()
        ws_bob = await bob.connect_websocket()
        print("   ✅ Both connected")

        # Join conversations
        await alice.join_conversation(ws_alice, conv_id)
        await bob.join_conversation(ws_bob, conv_id)

        # Wait for join confirmations
        await asyncio.sleep(0.2)
        print("   ✅ Both joined conversation")

        # Set up message handlers
        received_messages = []

        async def handle_alice_messages():
            async for message in ws_alice:
                data = json.loads(message)
                if data.get("type") == "message":
                    received_messages.append(("alice", data["message"]["content"]))
                    print(f"   📨 Alice received: {data['message']['content']}")

        async def handle_bob_messages():
            async for message in ws_bob:
                data = json.loads(message)
                if data.get("type") == "message":
                    received_messages.append(("bob", data["message"]["content"]))
                    print(f"   📨 Bob received: {data['message']['content']}")

        # Start message handlers
        alice_task = asyncio.create_task(handle_alice_messages())
        bob_task = asyncio.create_task(handle_bob_messages())

        await asyncio.sleep(0.3)

        # Send messages
        print("\n💬 Sending messages...")
        await alice.send_websocket_message(ws_alice, conv_id, "Hi Bob!")
        await asyncio.sleep(0.5)

        await bob.send_websocket_message(ws_bob, conv_id, "Hi Alice!")
        await asyncio.sleep(0.5)

        print(f"\n✅ Received {len(received_messages)} messages")

        # Cleanup
        await ws_alice.close()
        await ws_bob.close()
        alice_task.cancel()
        bob_task.cancel()

    finally:
        await alice.close()
        await bob.close()


async def example_token_refresh():
    """Example: Token refresh."""
    print("\n" + "=" * 60)
    print("Example 3: Token Refresh")
    print("=" * 60)

    client = PneumaticClient()

    try:
        await client.signup("refresh_user", "pass123")
        await client.login("refresh_user", "pass123")

        print(f"\n✅ Logged in")
        print(f"   Access token: {client.access_token[:20]}...")
        print(f"   Refresh token: {client.refresh_token[:20]}...")

        # Refresh tokens
        print("\n🔄 Refreshing tokens...")
        await client.refresh_tokens()
        print(f"   ✅ New access token: {client.access_token[:20]}...")
        print(f"   ✅ New refresh token: {client.refresh_token[:20]}...")

    finally:
        await client.close()


async def example_list_conversations():
    """Example: List and browse conversations."""
    print("\n" + "=" * 60)
    print("Example 4: List Conversations")
    print("=" * 60)

    client = PneumaticClient()

    try:
        await client.signup("list_user", "pass123")
        await client.login("list_user", "pass123")

        # Create multiple conversations
        print("\n📝 Creating conversations...")
        conv1 = await client.create_conversation("Chat 1")
        conv2 = await client.create_conversation("Chat 2")
        conv3 = await client.create_conversation("Chat 3")
        print(f"   ✅ Created 3 conversations")

        # List all conversations
        print("\n📋 Listing conversations...")
        conversations = await client.list_conversations()
        print(f"   ✅ Found {len(conversations)} conversation(s):")
        for conv in conversations:
            print(f"      - {conv['title']} (ID: {conv['id']})")

    finally:
        await client.close()


async def main():
    """Run all examples."""
    print("\n" + "🚀 Pneumatic Chat - Complete Examples" + "\n")

    try:
        await example_basic_usage()
        await example_websocket_chat()
        await example_token_refresh()
        await example_list_conversations()

        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
