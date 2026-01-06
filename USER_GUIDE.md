# Pneumatic Chat - User Guide

A comprehensive guide to using all features of the Pneumatic chat application.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Conversations](#conversations)
4. [Real-Time Messaging](#real-time-messaging)
5. [Advanced Features](#advanced-features)
6. [API Reference](#api-reference)

---

## Getting Started

### 1. Start the Server

```bash
# Make sure you're in the project directory
cd /Users/jingxuanyang/Projects/Pneumatic

# Activate virtual environment (if using one)
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Start the server
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### 2. Access the Web Interface

Open `index.html` in your browser, or navigate to:
- Login/Signup: `http://localhost:8000` (if serving static files)
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- Alternative API Docs: `http://localhost:8000/redoc`

---

## Authentication

### Sign Up (Create Account)

**Using Web UI:**
1. Open `index.html`
2. Click "Sign Up" tab
3. Enter username and password
4. Click "Create Account"

**Using API:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "id": "user-uuid-here",
  "username": "alice"
}
```

### Login

**Using Web UI:**
1. Enter username and password
2. Click "Login"
3. You'll be redirected to the chat page

**Using API:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save these tokens!** You'll need the `access_token` for authenticated requests.

### Using Tokens

All protected endpoints require the access token in the Authorization header:

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token

When your access token expires (after 30 minutes), use the refresh token:

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Response:** New access and refresh tokens.

---

## Conversations

### Create a Conversation

**Using Web UI:**
1. Click "+ New Conversation" button
2. Enter conversation title
3. Enter member usernames (comma-separated)
4. Click "Create"

**Using API:**
```bash
curl -X POST "http://localhost:8000/conversations" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Chat",
    "member_ids": ["user-id-1", "user-id-2"]
  }'
```

**Note:** You are automatically added as a member, even if not in `member_ids`.

**Response:**
```json
{
  "id": "conv-uuid-here",
  "title": "Team Chat",
  "members": ["your-user-id", "user-id-1", "user-id-2"]
}
```

### List Your Conversations

**Using Web UI:**
- Conversations appear automatically in the sidebar

**Using API:**
```bash
curl -X GET "http://localhost:8000/conversations" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv-1",
      "title": "Team Chat",
      "members": ["user-1", "user-2"]
    }
  ]
}
```

### Get Messages from a Conversation

```bash
curl -X GET "http://localhost:8000/conversations/{conversation_id}/messages?limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-1",
      "message_id": "client-uuid",
      "sender_id": "user-1",
      "conversation_id": "conv-1",
      "content": "Hello!",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

## Real-Time Messaging

### WebSocket Connection

**Using Web UI:**
- WebSocket connects automatically after login
- Just select a conversation and start typing!

**Using JavaScript:**
```javascript
// Get token first (from login)
const token = "YOUR_ACCESS_TOKEN";

// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  console.log("Connected!");

  // Join a conversation
  ws.send(JSON.stringify({
    type: "join",
    conversation_id: "conv-id-here"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);

  if (data.type === "message") {
    console.log("New message:", data.message.content);
  }
};
```

### Send a Message via WebSocket

```javascript
// After joining a conversation
ws.send(JSON.stringify({
  type: "message",
  message_id: crypto.randomUUID(),  // Generate unique ID
  conversation_id: "conv-id-here",
  content: "Hello everyone!"
}));
```

### Send a Message via HTTP API

```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "unique-uuid-here",
    "sender_id": "your-user-id",
    "conversation_id": "conv-id-here",
    "content": "Hello from HTTP!"
  }'
```

**Note:** `sender_id` must match your authenticated user ID.

---

## Advanced Features

### Message Idempotency

The `message_id` field prevents duplicate messages. If you send the same `message_id` twice, the server returns the existing message instead of creating a duplicate.

**Example:**
```javascript
const messageId = "fixed-id-123";

// First send
ws.send(JSON.stringify({
  type: "message",
  message_id: messageId,
  conversation_id: "conv-1",
  content: "Hello"
}));

// Retry with same message_id (e.g., after network error)
ws.send(JSON.stringify({
  type: "message",
  message_id: messageId,  // Same ID
  conversation_id: "conv-1",
  content: "Hello"
}));
// Server returns the original message, no duplicate created
```

### Multiple Devices

Users can connect from multiple devices simultaneously:
- Phone, laptop, tablet all receive messages in real-time
- Each device maintains its own WebSocket connection
- All devices receive broadcasts automatically

### Redis Pub/Sub (Multi-Instance)

If you have Redis running, you can run multiple server instances:

**Terminal 1:**
```bash
uvicorn main:app --port 8000
```

**Terminal 2:**
```bash
uvicorn main:app --port 8001
```

**How it works:**
- User connects to instance 1 (port 8000)
- User connects to instance 2 (port 8001)
- Message sent from instance 1 → Redis → Instance 2 receives it
- Both users get the message in real-time

**Test it:**
1. Open two browser windows
2. Connect one to `http://localhost:8000`
3. Connect the other to `http://localhost:8001`
4. Join the same conversation in both
5. Send a message from one → both receive it!

### Presence Tracking

**Check if users are online:**
```python
from app.pubsub import PresenceManager
from redis.asyncio import Redis

redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
presence = PresenceManager(redis)

# Check single user
is_online = await presence.is_online("user-id")

# Check multiple users
online_users = await presence.get_online_users(["user-1", "user-2", "user-3"])
# Returns: ["user-1", "user-2"]  (only online ones)
```

**How it works:**
- When user connects → presence key created in Redis
- Key expires after 5 minutes (TTL)
- If user disconnects → key removed immediately
- If user crashes → key expires automatically

---

## Complete Example: Full Chat Flow

### Step 1: Create Users

```bash
# User 1
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass123"}'

# User 2
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "pass123"}'
```

### Step 2: Login and Get Tokens

```bash
# Alice logs in
ALICE_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass123"}' | jq -r '.access_token')

# Bob logs in
BOB_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "pass123"}' | jq -r '.access_token')
```

### Step 3: Get User IDs

```bash
ALICE_ID=$(curl -s -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq -r '.id')

BOB_ID=$(curl -s -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $BOB_TOKEN" | jq -r '.id')
```

### Step 4: Create Conversation

```bash
CONV_ID=$(curl -s -X POST "http://localhost:8000/conversations" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Alice & Bob Chat\", \"member_ids\": [\"$BOB_ID\"]}" | jq -r '.id')
```

### Step 5: Connect WebSockets

**Terminal 1 (Alice):**
```javascript
const ws1 = new WebSocket(`ws://localhost:8000/ws?token=${ALICE_TOKEN}`);
ws1.onopen = () => {
  ws1.send(JSON.stringify({
    type: "join",
    conversation_id: CONV_ID
  }));
};
ws1.onmessage = (e) => console.log("Alice received:", JSON.parse(e.data));
```

**Terminal 2 (Bob):**
```javascript
const ws2 = new WebSocket(`ws://localhost:8000/ws?token=${BOB_TOKEN}`);
ws2.onopen = () => {
  ws2.send(JSON.stringify({
    type: "join",
    conversation_id: CONV_ID
  }));
};
ws2.onmessage = (e) => console.log("Bob received:", JSON.parse(e.data));
```

### Step 6: Send Messages

**Alice sends:**
```javascript
ws1.send(JSON.stringify({
  type: "message",
  message_id: crypto.randomUUID(),
  conversation_id: CONV_ID,
  content: "Hi Bob!"
}));
```

**Bob receives it automatically!**

---

## API Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Create new account | No |
| POST | `/auth/login` | Login and get tokens | No |
| POST | `/auth/refresh` | Refresh access token | No |
| GET | `/auth/me` | Get current user info | Yes |

### Conversation Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/conversations` | List user's conversations | Yes |
| POST | `/conversations` | Create new conversation | Yes |
| GET | `/conversations/{id}/messages` | Get messages | Yes |
| POST | `/messages` | Send message (HTTP) | Yes |

### WebSocket

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/ws?token=...` | Real-time messaging | Yes (token in query) |

### WebSocket Message Types

**Client → Server:**
```json
// Join conversation
{"type": "join", "conversation_id": "conv-id"}

// Send message
{
  "type": "message",
  "message_id": "uuid",
  "conversation_id": "conv-id",
  "content": "Hello!"
}
```

**Server → Client:**
```json
// Joined confirmation
{"type": "joined", "conversation_id": "conv-id"}

// New message
{
  "type": "message",
  "message": {
    "id": "msg-id",
    "message_id": "client-uuid",
    "sender_id": "user-id",
    "conversation_id": "conv-id",
    "content": "Hello!",
    "created_at": "2024-01-01T12:00:00Z"
  }
}

// Error
{"type": "error", "reason": "error message"}
```

---

## Common Patterns

### Pattern 1: Auto-Reconnect WebSocket

```javascript
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket(token) {
  ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

  ws.onopen = () => {
    console.log("Connected!");
    reconnectAttempts = 0;
    // Rejoin conversations
    joinedConversations.forEach(convId => {
      ws.send(JSON.stringify({
        type: "join",
        conversation_id: convId
      }));
    });
  };

  ws.onclose = () => {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      console.log(`Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`);
      setTimeout(() => connectWebSocket(token), 1000 * reconnectAttempts);
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };
}
```

### Pattern 2: Token Refresh Before Expiry

```javascript
let accessToken = localStorage.getItem('accessToken');
let refreshToken = localStorage.getItem('refreshToken');

// Refresh token 5 minutes before expiry (tokens last 30 minutes)
setInterval(async () => {
  try {
    const response = await fetch('http://localhost:8000/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      accessToken = data.access_token;
      refreshToken = data.refresh_token;
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      console.log('Tokens refreshed');
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
}, 25 * 60 * 1000); // Every 25 minutes
```

### Pattern 3: Message Queue (Offline Support)

```javascript
const messageQueue = [];

function sendMessage(convId, content) {
  const message = {
    type: "message",
    message_id: crypto.randomUUID(),
    conversation_id: convId,
    content: content
  };

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  } else {
    // Queue for later
    messageQueue.push(message);
    console.log("Message queued (offline)");
  }
}

// When WebSocket reconnects
ws.onopen = () => {
  // Send queued messages
  messageQueue.forEach(msg => {
    ws.send(JSON.stringify(msg));
  });
  messageQueue = [];
};
```

---

## Troubleshooting

### "401 Unauthorized" Error

**Problem:** Token expired or invalid

**Solution:**
1. Check token is still valid: `GET /auth/me`
2. If expired, refresh: `POST /auth/refresh`
3. Update your stored token

### WebSocket Connection Fails

**Problem:** Can't connect to WebSocket

**Solutions:**
1. Check token is valid
2. Verify token is in query: `ws://localhost:8000/ws?token=...`
3. Check server is running
4. Check browser console for errors

### Messages Not Received

**Problem:** Sent message but not received

**Solutions:**
1. Verify you joined the conversation
2. Check you're a member of the conversation
3. Verify WebSocket is connected: `ws.readyState === WebSocket.OPEN`
4. Check server logs for errors

### Redis Connection Issues

**Problem:** Redis errors in logs

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify Redis URL: `echo $REDIS_URL`
3. App will fall back to local broadcast if Redis unavailable

---

## Best Practices

1. **Always generate unique `message_id`** - Use `crypto.randomUUID()` or similar
2. **Handle token expiry** - Refresh tokens before they expire
3. **Reconnect WebSocket** - Implement auto-reconnect logic
4. **Queue messages offline** - Store messages when disconnected
5. **Validate user input** - Check conversation membership before sending
6. **Error handling** - Always handle WebSocket errors gracefully
7. **Security** - Never expose tokens in client-side code (use environment variables in production)

---

## Next Steps

1. ✅ Try the web UI (`index.html`)
2. ✅ Test API endpoints with curl or Postman
3. ✅ Build your own client using the WebSocket API
4. ✅ Set up Redis for multi-instance testing
5. ✅ Explore the API docs at `/docs`

Happy chatting! 💬
