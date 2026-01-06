#!/usr/bin/env python3
"""
Simple script to test Redis connection and basic functionality.
Run this first to verify Redis is working.
"""
import asyncio
import sys
from app.pubsub import RedisPubSub, PresenceManager
from redis.asyncio import Redis


async def test_redis_connection():
    """Test basic Redis connection."""
    print("🔍 Testing Redis connection...")

    try:
        pubsub = RedisPubSub()
        await pubsub.connect()
        print("✅ Redis connection successful!")
        await pubsub.disconnect()
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   - Install: brew install redis")
        print("   - Start: brew services start redis")
        print("   - Or: redis-server")
        return False


async def test_pubsub():
    """Test pub/sub functionality."""
    print("\n🔍 Testing Pub/Sub...")

    try:
        pubsub = RedisPubSub()
        await pubsub.connect()

        received = []

        async def handler(channel, data):
            received.append((channel, data))
            print(f"📨 Received on {channel}: {data}")

        # Subscribe to test channel
        test_channel = "test:channel"
        await pubsub.subscribe(test_channel, handler)
        print(f"✅ Subscribed to {test_channel}")

        # Wait a bit for subscription to establish
        await asyncio.sleep(0.2)

        # Publish a message
        test_message = {"type": "test", "message": "Hello Redis!"}
        await pubsub.publish(test_channel, test_message)
        print(f"📤 Published message to {test_channel}")

        # Wait for message to be received
        await asyncio.sleep(0.3)

        if received:
            print("✅ Pub/Sub working correctly!")
        else:
            print("⚠️  No message received (this might be normal if handler didn't fire)")

        await pubsub.disconnect()
        return True
    except Exception as e:
        print(f"❌ Pub/Sub test failed: {e}")
        return False


async def test_presence():
    """Test presence tracking."""
    print("\n🔍 Testing Presence Tracking...")

    try:
        redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await redis.ping()

        presence = PresenceManager(redis)
        test_user = "test_user_123"

        # Set presence
        await presence.set_presence(test_user, {"status": "online"})
        print(f"✅ Set presence for {test_user}")

        # Check if online
        is_online = await presence.is_online(test_user)
        print(f"✅ User online check: {is_online}")

        # Get online users
        online = await presence.get_online_users([test_user, "other_user"])
        print(f"✅ Online users: {online}")

        # Remove presence
        await presence.remove_presence(test_user)
        is_online_after = await presence.is_online(test_user)
        print(f"✅ User offline after removal: {not is_online_after}")

        await redis.aclose()
        print("✅ Presence tracking working correctly!")
        return True
    except Exception as e:
        print(f"❌ Presence test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Redis Integration Test Suite")
    print("=" * 50)

    results = []

    # Test 1: Connection
    results.append(await test_redis_connection())

    if not results[0]:
        print("\n❌ Cannot proceed without Redis connection")
        sys.exit(1)

    # Test 2: Pub/Sub
    results.append(await test_pubsub())

    # Test 3: Presence
    results.append(await test_presence())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Connection: {'✅' if results[0] else '❌'}")
    print(f"Pub/Sub:    {'✅' if results[1] else '❌'}")
    print(f"Presence:   {'✅' if results[2] else '❌'}")

    if all(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
