# Tutorial: Complete Feature Guide

Comprehensive guide to using and understanding Pneumatic Chat.

## Table of Contents

1. [Authentication](#authentication)
2. [Conversations](#conversations)
3. [Real-Time Messaging](#real-time-messaging)
4. [API Reference](#api-reference)
5. [Codebase Overview](#codebase-overview)
6. [Architecture](#architecture)

---

## Authentication

### Sign Up

**Web UI:**
1. Visit `http://localhost:8000`
2. Click "Sign Up" tab
3. Enter username, password, and optional full name
4. Click "Create Account"

**API:**
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

**Web UI:**
1. Enter username and password
2. Click "Login"
3. Redirected to chat interface

**API:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'
```

**Response:**
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
- Store tokens in `Authorization: Bearer <token>` header

### Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

## Conversations

### 1-on-1 Conversations

**How to Start:**
1. In the **Users** section, click on a user
2. A 1-on-1 conversation is created automatically
3. If a conversation already exists, it opens that one
4. Start chatting!

**Features:**
- Automatically shows the other person's name
- No duplicate conversations (reuses existing)
- Real-time message updates

**API:**
```bash
curl -X POST "http://localhost:8000/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "member_ids": ["other-user-id"]
  }'
```

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

**API:**
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

ws.onopen = () => {
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
};

ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === "message") {
    console.log("Received:", data.message);
  }
};
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
- Messages are displayed with sender name and timestamp
- Your own messages appear on the right, others on the left

---

## API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Create new account |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |

### Conversation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/conversations` | List user's conversations |
| POST | `/conversations` | Create conversation |
| GET | `/conversations/{id}/messages` | Get messages from conversation |

### Message Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/messages` | Send message |

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |

### Observability Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/metrics` | Prometheus metrics |

---

## Codebase Overview

### Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM for database operations
- **SQLite** (dev) / **PostgreSQL** (prod) - Database
- **WebSockets** - Real-time bidirectional communication
- **JWT** - Token-based authentication
- **Argon2** - Secure password hashing
- **Pydantic** - Data validation and serialization
- **OpenTelemetry** - Distributed tracing
- **Prometheus** - Metrics format

### Core Files

**`app/models.py`** - Database Models
- `User` - User accounts (id, username, full_name, password_hash)
- `Conversation` - Chat rooms (id, title)
- `ConversationMember` - Links users to conversations
- `Message` - Chat messages

**`app/schemas.py`** - Data Validation
- Pydantic models for request/response validation

**`app/auth.py`** - Authentication
- JWT token creation/validation
- Password hashing (Argon2)
- `get_current_user()` - HTTP route dependency
- `get_current_user_websocket()` - WebSocket authentication

**`app/store_sql.py`** - Database Operations
- Async database operations
- User CRUD operations
- Conversation management
- Message storage

**`app/routes.py`** - REST API Endpoints
- Protected API routes for conversations and messages

**`app/auth_routes.py`** - Authentication Endpoints
- Signup, login, refresh, get current user

**`app/websockets.py`** - WebSocket Manager
- Manages WebSocket connections
- Broadcasts messages to conversation members

**`app/main.py`** - Application Entry Point
- FastAPI application setup
- WebSocket endpoint (`/ws`)
- Health checks and metrics
- Observability setup

**`app/metrics.py`** - Metrics Collection
- Tracks WebSocket connections and messages
- Prometheus format export

**`app/logging_config.py`** - Structured Logging
- JSON-formatted logging configuration

**`app/tracing.py`** - OpenTelemetry Tracing
- Request tracing setup

**`app/rate_limit.py`** - Rate Limiting
- Per-user/IP rate limiting middleware

### Frontend Files

**`static/index.html`** - Login/Signup Page
- User registration and login
- Token storage in localStorage

**`static/chat.html`** - Main Chat Interface
- Displays conversations list
- Real-time message display
- WebSocket connection management

---

## Architecture

### Authentication Flow

1. User signs up → Password hashed with Argon2
2. User logs in → Receives JWT access and refresh tokens
3. Tokens stored in localStorage
4. API requests use `Authorization: Bearer <token>` header
5. WebSocket uses `?token=<token>` query parameter

### Conversation Flow

**1-on-1 Chat:**
1. User clicks on another user
2. Frontend calls `POST /conversations` with other user's ID
3. Backend checks for existing 1-on-1 conversation
4. Returns existing or creates new conversation

**Group Chat:**
1. User clicks "+ New Group Chat"
2. Enters group name and participant usernames
3. Frontend resolves usernames to user IDs
4. Calls `POST /conversations` with member IDs
5. Backend creates group conversation

### Message Flow

1. Client sends message via HTTP or WebSocket
2. Backend validates sender is conversation member
3. Message saved to database
4. Broadcasted via WebSocket to all conversation members
5. Frontend updates UI automatically

### Real-time Updates

1. WebSocket connection established
2. Client joins conversation: `{"type": "join", "conversation_id": "..."}`
3. Messages broadcasted to all active connections
4. Frontend updates UI automatically
5. New conversations appear when messages received

### Observability

- **Health Checks**: `/health` (always up), `/ready` (database check)
- **Metrics**: Prometheus format at `/metrics`
- **Logging**: Structured JSON logs
- **Tracing**: OpenTelemetry spans
- **Rate Limiting**: Per-user/IP limits with headers

---

## Key Concepts

### Conversation Types
- **1-on-1**: Exactly 2 members, shows other user's name
- **Group**: 3+ members, shows group title with 👥 icon

### Message Broadcasting
- Messages sent to all active WebSocket connections for conversation members
- Supports multiple devices per user
- Idempotent via `message_id` field

### Security
- JWT tokens with expiration
- Argon2 password hashing
- Rate limiting per user/IP
- CORS configuration

---

## Testing

Run tests with:
```bash
pytest
```

Test files:
- `tests/test_app.py` - Core functionality tests
- `tests/test_auth.py` - Authentication tests

---

## Production Considerations

1. **Database**: Use PostgreSQL in production (set `DATABASE_URL`)
2. **Security**: Set `SECRET_KEY` environment variable (minimum 32 characters)
3. **Logging**: JSON logs can be sent to log aggregation services
4. **Tracing**: Configure OTLP exporter for production
5. **Rate Limiting**: Consider Redis-backed limiter for multi-instance deployments
6. **CORS**: Update `allow_origins` in `main.py` for production
