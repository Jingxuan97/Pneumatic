#!/usr/bin/env python3
"""
Test script to simulate multi-instance message flow.
This demonstrates how messages flow between different server instances via Redis.
"""
import asyncio
import json
from app.pubsub import RedisPubSub
from app.store_sql import store


async def simulate_node(node_id: str, conversation_id: str, user_ids: list):
    """
    Simulate a server node that receives and forwards messages.

    Args:
        node_id: Identifier for this node
        conversation_id: Conversation to subscribe to
        user_ids: List of user IDs connected to this node
    """
    print(f"\n🖥️  Node {node_id} starting...")
    print(f"   Users: {user_ids}")

    pubsub = RedisPubSub()
    await pubsub.connect()

    received_messages = []

    async def message_handler(channel: str, data: dict):
        """Handle messages received from Redis."""
        print(f"📨 Node {node_id} received: {data.get('message', {}).get('content', 'N/A')}")
        received_messages.append(data)

        # Simulate forwarding to local WebSocket connections
        print(f"   → Forwarding to local users: {user_ids}")

    # Subscribe to conversation channel
    channel = pubsub.get_channel_name(conversation_id)
    await pubsub.subscribe(channel, message_handler)
    print(f"✅ Node {node_id} subscribed to {channel}")

    return pubsub, received_messages


async def test_multi_instance_flow():
    """Test message flow between multiple instances."""
    print("=" * 60)
    print("Multi-Instance Message Flow Test")
    print("=" * 60)

    # Create test conversation
    print("\n📝 Creating test conversation...")
    try:
        # Create test users first
        user1_id = "test_user_1"
        user2_id = "test_user_2"

        # Note: In real scenario, users would be created via API
        # For this test, we'll use a mock conversation ID
        conversation_id = "test_conv_multi_instance"

        print(f"✅ Using conversation: {conversation_id}")
    except Exception as e:
        print(f"❌ Failed to setup: {e}")
        return

    # Simulate two nodes
    print("\n🔄 Starting two server nodes...")

    node1_pubsub, node1_messages = await simulate_node(
        "Node-1",
        conversation_id,
        [user1_id]
    )

    node2_pubsub, node2_messages = await simulate_node(
        "Node-2",
        conversation_id,
        [user2_id]
    )

    # Wait for subscriptions to establish
    await asyncio.sleep(0.3)

    # Node 1 publishes a message
    print(f"\n📤 Node-1 publishing message...")
    message = {
        "type": "message",
        "message": {
            "id": "msg_1",
            "content": "Hello from Node-1!",
            "conversation_id": conversation_id,
            "sender_id": user1_id
        }
    }

    channel = node1_pubsub.get_channel_name(conversation_id)
    await node1_pubsub.publish(channel, message)
    print(f"✅ Message published to {channel}")

    # Wait for messages to propagate
    await asyncio.sleep(0.5)

    # Check results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Node-1 received: {len(node1_messages)} messages")
    print(f"Node-2 received: {len(node2_messages)} messages")

    if len(node2_messages) > 0:
        print("\n✅ SUCCESS: Message flowed from Node-1 to Node-2 via Redis!")
        print(f"   Node-2 received: {node2_messages[0].get('message', {}).get('content')}")
    else:
        print("\n❌ FAILED: Node-2 did not receive the message")

    # Cleanup
    await node1_pubsub.disconnect()
    await node2_pubsub.disconnect()
    print("\n✅ Test complete")


async def test_presence_across_nodes():
    """Test presence tracking across multiple nodes."""
    print("\n" + "=" * 60)
    print("Presence Tracking Across Nodes Test")
    print("=" * 60)

    from redis.asyncio import Redis
    from app.pubsub import PresenceManager

    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    presence = PresenceManager(redis)

    user1 = "user_node1"
    user2 = "user_node2"

    # Node 1: User 1 comes online
    print(f"\n🟢 Node-1: {user1} comes online")
    await presence.set_presence(user1)

    # Node 2: User 2 comes online
    print(f"🟢 Node-2: {user2} comes online")
    await presence.set_presence(user2)

    # Check online users from Node 1 perspective
    online = await presence.get_online_users([user1, user2, "user3"])
    print(f"\n📊 Online users: {online}")
    print(f"   Expected: [{user1}, {user2}]")

    if set(online) == {user1, user2}:
        print("✅ Presence tracking working across nodes!")
    else:
        print("❌ Presence tracking failed")

    # User 1 goes offline
    print(f"\n🔴 Node-1: {user1} goes offline")
    await presence.remove_presence(user1)

    online_after = await presence.get_online_users([user1, user2])
    print(f"📊 Online users after: {online_after}")

    if online_after == [user2]:
        print("✅ Presence removal working correctly!")
    else:
        print("❌ Presence removal failed")

    # Cleanup
    await presence.remove_presence(user2)
    await redis.aclose()


async def main():
    """Run all multi-instance tests."""
    try:
        # Test 1: Message flow
        await test_multi_instance_flow()

        # Test 2: Presence
        await test_presence_across_nodes()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
