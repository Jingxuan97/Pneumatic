#!/usr/bin/env python3
"""
Example usage of Redis pub/sub and presence in the Pneumatic chat application.
This demonstrates the key patterns used in the application.
"""
import asyncio
import json
from app.pubsub import RedisPubSub, PresenceManager
from redis.asyncio import Redis


async def example_pubsub_basic():
    """Basic pub/sub example."""
    print("=" * 60)
    print("Example 1: Basic Pub/Sub")
    print("=" * 60)

    pubsub = RedisPubSub()
    await pubsub.connect()

    # Message handler
    async def handle_message(channel: str, data: dict):
        print(f"📨 Received on {channel}: {data}")

    # Subscribe to a channel
    channel = "conv:chat_room_1"
    await pubsub.subscribe(channel, handle_message)
    print(f"✅ Subscribed to {channel}")

    # Wait for subscription
    await asyncio.sleep(0.2)

    # Publish a message
    message = {
        "type": "message",
        "message": {
            "content": "Hello from pub/sub!",
            "sender_id": "user_123"
        }
    }
    await pubsub.publish(channel, message)
    print(f"📤 Published message to {channel}")

    # Wait for message to be received
    await asyncio.sleep(0.3)

    await pubsub.disconnect()
    print("✅ Example complete\n")


async def example_presence_basic():
    """Basic presence tracking example."""
    print("=" * 60)
    print("Example 2: Presence Tracking")
    print("=" * 60)

    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    presence = PresenceManager(redis)

    user_id = "alice"

    # User comes online
    print(f"🟢 {user_id} comes online")
    await presence.set_presence(user_id, {"status": "active"})

    # Check if online
    is_online = await presence.is_online(user_id)
    print(f"   Is online: {is_online}")

    # Check multiple users
    users = ["alice", "bob", "charlie"]
    await presence.set_presence("bob")
    online_users = await presence.get_online_users(users)
    print(f"   Online users: {online_users}")

    # User goes offline
    print(f"🔴 {user_id} goes offline")
    await presence.remove_presence(user_id)

    is_online_after = await presence.is_online(user_id)
    print(f"   Is online: {is_online_after}")

    # Cleanup
    await presence.remove_presence("bob")
    await redis.aclose()
    print("✅ Example complete\n")


async def example_conversation_broadcast():
    """Example of broadcasting to a conversation."""
    print("=" * 60)
    print("Example 3: Conversation Broadcast")
    print("=" * 60)

    pubsub = RedisPubSub()
    await pubsub.connect()

    conversation_id = "conv_123"
    channel = pubsub.get_channel_name(conversation_id)

    # Simulate multiple nodes subscribing
    node1_messages = []
    node2_messages = []

    async def node1_handler(channel, data):
        node1_messages.append(data)
        print(f"📨 Node-1 received: {data['message']['content']}")

    async def node2_handler(channel, data):
        node2_messages.append(data)
        print(f"📨 Node-2 received: {data['message']['content']}")

    # Both nodes subscribe
    await pubsub.subscribe(channel, node1_handler)
    await asyncio.sleep(0.1)

    # Create second pubsub instance (simulating second node)
    pubsub2 = RedisPubSub()
    await pubsub2.connect()
    await pubsub2.subscribe(channel, node2_handler)

    await asyncio.sleep(0.2)

    # Publish message (from any node)
    message = {
        "type": "message",
        "message": {
            "content": "Hello everyone!",
            "conversation_id": conversation_id,
            "sender_id": "user_1"
        }
    }

    await pubsub.publish(channel, message)
    print(f"📤 Published to {channel}")

    # Wait for delivery
    await asyncio.sleep(0.3)

    print(f"   Node-1 received: {len(node1_messages)} messages")
    print(f"   Node-2 received: {len(node2_messages)} messages")

    await pubsub.disconnect()
    await pubsub2.disconnect()
    print("✅ Example complete\n")


async def example_presence_ttl():
    """Example of presence TTL expiration."""
    print("=" * 60)
    print("Example 4: Presence TTL")
    print("=" * 60)

    import os
    # Set short TTL for demo
    original_ttl = os.environ.get("PRESENCE_TTL_SECONDS")
    os.environ["PRESENCE_TTL_SECONDS"] = "2"  # 2 seconds

    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    presence = PresenceManager(redis)

    user_id = "temp_user"

    # Set presence
    await presence.set_presence(user_id)
    print(f"🟢 {user_id} online (TTL: 2 seconds)")

    is_online = await presence.is_online(user_id)
    print(f"   Is online: {is_online}")

    # Wait for TTL to expire
    print("⏳ Waiting for TTL to expire...")
    await asyncio.sleep(2.5)

    is_online_after = await presence.is_online(user_id)
    print(f"   Is online after TTL: {is_online_after}")

    if not is_online_after:
        print("✅ TTL expiration working correctly!")
    else:
        print("⚠️  TTL might not have expired yet")

    # Restore original TTL
    if original_ttl:
        os.environ["PRESENCE_TTL_SECONDS"] = original_ttl
    else:
        os.environ.pop("PRESENCE_TTL_SECONDS", None)

    await redis.aclose()
    print("✅ Example complete\n")


async def main():
    """Run all examples."""
    print("\n" + "🚀 Redis Pub/Sub and Presence Examples" + "\n")

    try:
        await example_pubsub_basic()
        await example_presence_basic()
        await example_conversation_broadcast()
        await example_presence_ttl()

        print("=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
