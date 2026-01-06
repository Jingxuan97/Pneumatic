# Pneumatic Chat - User Guide

Complete guide to using all features of the Pneumatic chat application.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Conversations](#conversations)
4. [Real-Time Messaging](#real-time-messaging)
5. [Observability](#observability)
6. [API Reference](#api-reference)

---

## Getting Started

### 1. Start the Server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 2. Access the Web Interface

Visit `http://localhost:8000` in your browser. The login page will be served automatically.

---

## Authentication

### Sign Up (Create Account)

**Using Web UI:**
1. Visit `http://localhost:8000`
2. Click "Sign Up" tab
3. Enter:
   - **Username** (required, unique)
   - **Password** (required)
   - **Full Name** (optional)
4. Click "Create Account"
5. You'll be automatically logged in!

**Using API:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123",
    "full_name": "Alice Smith"
  }'
```

### Login

**Using Web UI:**
1. Enter username and password
2. Click "Login"
3. You'll be redirected to the chat interface

**Using API:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'
```

Returns:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Token Management

- **Access Token**: Valid for 30 minutes, used for API requests
- **Refresh Token**: Valid for 7 days, used to get new access tokens
- Tokens are stored in browser `localStorage`
- Use `Authorization: Bearer <token>` header for API requests

### Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## Conversations

### 1-on-1 Conversations

**How to Start:**
1. In the **Users** section (sidebar), click on a user
2. A 1-on-1 conversation is created automatically
3. If a conversation already exists, it opens that one
4. Start chatting!

**Features:**
- Automatically shows the other person's name
- No duplicate conversations (reuses existing)
- Real-time message updates

### Group Conversations

**How to Create:**
1. Click **"+ New Group Chat"** button
2. Enter a **Group Name** (required)
3. Add participants by username (comma-separated)
   - Example: `bob, charlie, diana`
4. Click "Create Group"
5. The group chat is created with you as a member

**Features:**
- Shows group name with 👥 icon
- Supports any number of participants
- Host is automatically added as a member
- All members can send and receive messages

**Using API:**
```bash
curl -X POST "http://localhost:8000/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Team",
    "member_ids": ["user-id-1", "user-id-2"]
  }'
```

### Viewing Conversations

- All conversations appear in the sidebar
- 1-on-1 chats show the other person's name
- Group chats show the group name with 👥 icon
- Member count is displayed for all conversations
- New conversations appear automatically when you receive messages

---

## Real-Time Messaging

### Sending Messages

**Via Web UI:**
1. Select a conversation
2. Type your message in the input box
3. Press Enter or click "Send"
4. Message appears instantly for all participants

**Via WebSocket:**
```javascript
// Connect
const ws = new WebSocket(`ws://localhost:8000/ws?token=${accessToken}`);

// Join conversation
ws.send(JSON.stringify({
  type: "join",
  conversation_id: "conv-id"
}));

// Send message
ws.send(JSON.stringify({
  type: "message",
  message_id: crypto.randomUUID(),
  conversation_id: "conv-id",
  content: "Hello!"
}));
```

**Via HTTP API:**
```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "unique-id-123",
    "sender_id": "your-user-id",
    "conversation_id": "conv-id",
    "content": "Hello from API!"
  }'
```

### Receiving Messages

- Messages appear in real-time via WebSocket
- No page refresh needed
- Messages are displayed with:
  - Sender name (for group chats)
  - Message content
  - Timestamp
  - Visual distinction for your own messages

### Message Features

- **Idempotency**: Duplicate `message_id` prevents duplicate messages
- **Real-time**: Instant delivery to all participants
- **Multi-device**: Receive messages on all connected devices
- **Auto-discovery**: New conversations appear when messages are received

---

## Observability

### Health Checks

**Basic Health Check:**
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

**Readiness Check:**
```bash
curl http://localhost:8000/ready
# Returns: {"status": "ready"} or 503 if database unavailable
```

### Metrics (Prometheus Format)

```bash
curl http://localhost:8000/metrics
```

Returns Prometheus-formatted metrics:
- `pneumatic_websocket_connections_total` - Total connections established
- `pneumatic_websocket_connections_active` - Current active connections
- `pneumatic_messages_sent_total` - Total messages sent
- `pneumatic_messages_per_second` - Average messages/sec (60s window)

### Logging

- Structured JSON logs to stdout
- Includes: timestamp, level, logger, message, module, function, line
- Production-ready for log aggregation services

### Tracing

- OpenTelemetry instrumentation
- Automatic span creation for HTTP requests
- Console exporter (configurable for OTLP in production)

### Rate Limiting

- Default: 60 requests/minute, 1000 requests/hour per user/IP
- Response headers:
  - `X-RateLimit-Limit` - Maximum requests per minute
  - `X-RateLimit-Remaining` - Remaining requests
  - `X-RateLimit-Reset` - Unix timestamp when limit resets
- Exempt paths: `/health`, `/ready`, `/metrics`, `/docs`

---

## API Reference

### Authentication Endpoints

#### `POST /auth/signup`
Create a new user account.

**Request:**
```json
{
  "username": "alice",
  "password": "password123",
  "full_name": "Alice Smith"
}
```

**Response:** `201 Created`
```json
{
  "id": "user-id",
  "username": "alice",
  "full_name": "Alice Smith"
}
```

#### `POST /auth/login`
Authenticate and receive tokens.

**Request:**
```json
{
  "username": "alice",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `POST /auth/refresh`
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `GET /auth/me`
Get current user information.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "id": "user-id",
  "username": "alice",
  "full_name": "Alice Smith"
}
```

### Conversation Endpoints

#### `GET /conversations`
List all conversations for the current user.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "conversations": [
    {
      "id": "conv-id",
      "title": "Group Chat",
      "members": ["user-id-1", "user-id-2"]
    }
  ]
}
```

#### `POST /conversations`
Create a new conversation (1-on-1 or group).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "title": "Group Chat",
  "member_ids": ["user-id-1", "user-id-2"]
}
```

**Response:** `201 Created`
```json
{
  "id": "conv-id",
  "title": "Group Chat",
  "members": ["current-user-id", "user-id-1", "user-id-2"]
}
```

**Note:** Current user is automatically added as a member.

#### `GET /conversations/{conv_id}/messages`
Get messages from a conversation.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `limit` (optional, default: 50) - Number of messages to return

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "id": "msg-id",
      "message_id": "client-supplied-id",
      "sender_id": "user-id",
      "conversation_id": "conv-id",
      "content": "Hello!",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Message Endpoints

#### `POST /messages`
Send a message via HTTP.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "message_id": "unique-id-123",
  "sender_id": "your-user-id",
  "conversation_id": "conv-id",
  "content": "Hello!"
}
```

**Response:** `201 Created`
```json
{
  "id": "msg-id",
  "message_id": "unique-id-123",
  "sender_id": "your-user-id",
  "conversation_id": "conv-id",
  "content": "Hello!",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### User Endpoints

#### `GET /users`
List all registered users (excluding current user).

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": "user-id",
      "username": "bob",
      "full_name": "Bob Smith"
    }
  ]
}
```

### Observability Endpoints

#### `GET /health`
Basic health check.

**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

#### `GET /ready`
Readiness check (verifies database connectivity).

**Response:** `200 OK` or `503 Service Unavailable`
```json
{
  "status": "ready"
}
```

#### `GET /metrics`
Prometheus-formatted metrics.

**Response:** `200 OK` (text/plain)
```
# HELP pneumatic_websocket_connections_total Total number of WebSocket connections established
# TYPE pneumatic_websocket_connections_total counter
pneumatic_websocket_connections_total 42
...
```

### WebSocket Endpoint

#### `WS /ws?token=<access_token>`
WebSocket connection for real-time messaging.

**Authentication:** Token in query parameter or `Authorization` header

**Message Types:**

**Join Conversation:**
```json
{
  "type": "join",
  "conversation_id": "conv-id"
}
```

**Send Message:**
```json
{
  "type": "message",
  "message_id": "unique-id",
  "conversation_id": "conv-id",
  "content": "Hello!"
}
```

**Received Messages:**
```json
{
  "type": "message",
  "message": {
    "id": "msg-id",
    "message_id": "unique-id",
    "sender_id": "user-id",
    "conversation_id": "conv-id",
    "content": "Hello!",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Tips & Best Practices

1. **1-on-1 vs Group**: Click users for 1-on-1, use "+ New Group Chat" for groups
2. **Multiple Devices**: You can be logged in from multiple devices simultaneously
3. **Auto Discovery**: New conversations appear automatically when someone messages you
4. **Rate Limits**: Default is 60 requests/minute per user/IP
5. **Token Security**: Keep tokens secure, use refresh tokens for long-lived sessions
6. **Message IDs**: Always use unique IDs (e.g., `crypto.randomUUID()`) for idempotency
7. **Error Handling**: Check response status codes and handle errors gracefully

---

## Troubleshooting

### Can't log in
- Check username and password are correct
- Verify server is running
- Check browser console for errors

### Messages not appearing
- Verify WebSocket connection is established
- Check you've joined the conversation
- Verify you're a member of the conversation

### Rate limit errors
- Wait 60 seconds before retrying
- Check `X-RateLimit-Remaining` header
- Use exempt endpoints (`/health`, `/metrics`) for monitoring

### Database errors
- Check database is accessible
- Verify `DATABASE_URL` is set correctly
- Check `/ready` endpoint for database status

---

For more information, see:
- [Quick Start Guide](QUICK_START.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Codebase Explanation](CODEBASE_EXPLANATION.md)
