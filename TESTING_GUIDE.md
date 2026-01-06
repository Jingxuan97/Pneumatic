# Redis Testing Guide

This guide helps you test the Redis pub/sub and presence functionality.

## Prerequisites

1. **Install Redis** (if not already installed):
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Or start manually
   redis-server
   ```

2. **Verify Redis is running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Tests

### 1. Test Redis Connection

Run the basic connection test:

```bash
python test_redis_connection.py
```

This will test:
- ✅ Redis connection
- ✅ Pub/Sub functionality
- ✅ Presence tracking

**Expected output:**
```
==================================================
Redis Integration Test Suite
==================================================
🔍 Testing Redis connection...
✅ Redis connection successful!

🔍 Testing Pub/Sub...
✅ Subscribed to test:channel
📤 Published message to test:channel
📨 Received on test:channel: {'type': 'test', 'message': 'Hello Redis!'}
✅ Pub/Sub working correctly!

🔍 Testing Presence Tracking...
✅ Set presence for test_user_123
✅ User online check: True
✅ Online users: ['test_user_123']
✅ User offline after removal: True
✅ Presence tracking working correctly!

==================================================
Test Summary
==================================================
Connection: ✅
Pub/Sub:    ✅
Presence:   ✅

🎉 All tests passed!
```

### 2. Test Multi-Instance Message Flow

Simulate multiple server instances:

```bash
python test_multi_instance.py
```

This demonstrates:
- How messages flow between different nodes
- Redis pub/sub distribution
- Presence tracking across nodes

**Expected output:**
```
============================================================
Multi-Instance Message Flow Test
============================================================

🖥️  Node Node-1 starting...
   Users: ['test_user_1']
✅ Node Node-1 subscribed to conv:test_conv_multi_instance

🖥️  Node Node-2 starting...
   Users: ['test_user_2']
✅ Node Node-2 subscribed to conv:test_conv_multi_instance

📤 Node-1 publishing message...
✅ Message published to conv:test_conv_multi_instance
📨 Node Node-1 received: Hello from Node-1!
📨 Node Node-2 received: Hello from Node-1!

============================================================
Results
============================================================
Node-1 received: 1 messages
Node-2 received: 1 messages

✅ SUCCESS: Message flowed from Node-1 to Node-2 via Redis!
```

### 3. Run Examples

See practical usage examples:

```bash
python examples/redis_example.py
```

This shows:
- Basic pub/sub patterns
- Presence tracking
- Conversation broadcasting
- TTL expiration

## Manual Testing with Real Server

### Step 1: Start Redis

```bash
redis-server
```

### Step 2: Start First Server Instance

Terminal 1:
```bash
uvicorn main:app --port 8000
```

### Step 3: Start Second Server Instance

Terminal 2:
```bash
uvicorn main:app --port 8001
```

### Step 4: Test with Browser

1. **Open two browser windows/tabs**

2. **Window 1** (connects to port 8000):
   - Open `http://localhost:8000` (or use `index.html`)
   - Sign up: `alice` / `password123`
   - Create a conversation

3. **Window 2** (connects to port 8001):
   - Open `http://localhost:8001` (or use `index.html`)
   - Sign up: `bob` / `password123`
   - Join the same conversation

4. **Send messages**:
   - Send from Window 1 (alice)
   - Verify Window 2 (bob) receives it via Redis pub/sub

### Step 5: Monitor Redis

In a third terminal:
```bash
# Monitor Redis commands
redis-cli MONITOR

# Check presence keys
redis-cli KEYS "presence:*"

# Check pub/sub channels
redis-cli PUBSUB CHANNELS "conv:*"
```

## Testing Presence

### Check Online Users

```python
from redis.asyncio import Redis
from app.pubsub import PresenceManager

redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
presence = PresenceManager(redis)

# Check if user is online
is_online = await presence.is_online("user_id")

# Get online users from a list
online = await presence.get_online_users(["user1", "user2", "user3"])
```

### Test TTL Expiration

```bash
# Set presence with short TTL
redis-cli SETEX "presence:test_user" 5 "{}"

# Check immediately (should exist)
redis-cli EXISTS "presence:test_user"

# Wait 6 seconds, then check (should be gone)
redis-cli EXISTS "presence:test_user"
```

## Troubleshooting

### Redis Connection Failed

**Error:** `Connection refused` or `Redis not available`

**Solution:**
1. Check Redis is running: `redis-cli ping`
2. Verify Redis URL: `echo $REDIS_URL` (default: `redis://localhost:6379/0`)
3. Check Redis logs: `tail -f /usr/local/var/log/redis.log`

### Messages Not Flowing

**Symptoms:** Messages only work within same instance

**Check:**
1. Both instances connected to same Redis
2. Channels are being subscribed: `redis-cli PUBSUB CHANNELS`
3. Messages are being published: `redis-cli MONITOR`

### Presence Not Working

**Symptoms:** Users always appear offline

**Check:**
1. Presence keys exist: `redis-cli KEYS "presence:*"`
2. TTL is set: `redis-cli TTL "presence:user_id"`
3. App logs for errors

## Running Tests

Run the full test suite:

```bash
# All tests
pytest tests/test_redis_pubsub.py -v

# Specific test
pytest tests/test_redis_pubsub.py::test_redis_connection -v

# With output
pytest tests/test_redis_pubsub.py -v -s
```

## Next Steps

1. ✅ Verify Redis connection works
2. ✅ Test pub/sub message flow
3. ✅ Test presence tracking
4. ✅ Test multi-instance scenario
5. ✅ Integrate with your application

For more details, see `REDIS_SETUP.md`.
