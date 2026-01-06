# Redis Pub/Sub and Presence Setup

## Overview

The application now uses Redis for:
1. **Pub/Sub messaging** - Broadcast messages across multiple server instances
2. **Presence tracking** - Track which users are online with TTL-based expiration

## Architecture

### Pub/Sub Pattern
- Each conversation has a Redis channel: `conv:{conversation_id}`
- When a message is sent, it's published to the conversation's channel
- All server instances subscribe to channels for conversations their users have joined
- Messages received from Redis are forwarded to local WebSocket connections

### Presence Tracking
- User presence stored as Redis keys: `presence:{user_id}`
- Keys have TTL (default: 5 minutes)
- Automatically expire when user goes offline
- Can query which users from a list are online

## Setup

### 1. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Redis URL (Optional)

By default, the app connects to `redis://localhost:6379/0`.

To use a different Redis instance:
```bash
export REDIS_URL="redis://localhost:6379/0"
```

### 4. Configure Presence TTL (Optional)

Default TTL is 300 seconds (5 minutes):
```bash
export PRESENCE_TTL_SECONDS="300"
```

## Running Multiple Instances

To test multi-instance message flow:

### Terminal 1:
```bash
uvicorn main:app --reload --port 8000
```

### Terminal 2:
```bash
uvicorn main:app --reload --port 8001
```

### Test:
1. Connect to instance 1 (port 8000)
2. Connect to instance 2 (port 8001)
3. Join the same conversation from both
4. Send a message from instance 1
5. Verify instance 2 receives it via Redis pub/sub

## How It Works

### Message Flow

1. **User sends message** via WebSocket to Node A
2. **Node A** saves message to database
3. **Node A** publishes message to Redis channel `conv:{conversation_id}`
4. **All nodes** subscribed to that channel receive the message
5. **Each node** forwards message to local WebSocket connections for conversation members

### Presence Flow

1. **User connects** → Presence key created in Redis with TTL
2. **User active** → Presence TTL refreshed periodically
3. **User disconnects** → Presence key deleted
4. **TTL expires** → Presence automatically removed (handles crashes)

## Fallback Behavior

If Redis is not available:
- App falls back to local in-process broadcasting
- Presence tracking is disabled
- Multi-instance messaging won't work (messages only within same process)

## Testing

Run Redis pub/sub tests:
```bash
pytest tests/test_redis_pubsub.py -v
```

**Note:** Tests require Redis to be running. If Redis is not available, tests will be skipped.

## Production Considerations

1. **Redis High Availability**: Use Redis Sentinel or Cluster for production
2. **Connection Pooling**: Redis client handles connection pooling automatically
3. **Monitoring**: Monitor Redis memory usage and connection count
4. **TTL Tuning**: Adjust `PRESENCE_TTL_SECONDS` based on your needs
5. **Channel Cleanup**: Channels are automatically cleaned up when no subscribers

## Troubleshooting

### Redis Connection Failed
- Check Redis is running: `redis-cli ping`
- Verify Redis URL in environment variables
- Check firewall/network settings

### Messages Not Flowing Between Instances
- Verify both instances are connected to same Redis
- Check Redis logs for errors
- Ensure channels are being subscribed to

### Presence Not Working
- Check Redis keys: `redis-cli KEYS "presence:*"`
- Verify TTL is set: `redis-cli TTL "presence:user_id"`
- Check application logs for errors
