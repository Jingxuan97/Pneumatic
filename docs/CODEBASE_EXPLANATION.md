# Codebase Explanation

A simplified guide to understanding the Pneumatic Chat codebase.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM for database operations
- **SQLite** (dev) / **PostgreSQL** (prod) - Database
- **WebSockets** - Real-time bidirectional communication
- **JWT** - Token-based authentication
- **Argon2** - Secure password hashing
- **Pydantic** - Data validation and serialization
- **OpenTelemetry** - Distributed tracing
- **Prometheus** - Metrics format

---

## Core Files

### `app/models.py` - Database Models
Defines database schema using SQLAlchemy:
- `User` - User accounts (id, username, full_name, password_hash)
- `Conversation` - Chat rooms (id, title)
- `ConversationMember` - Links users to conversations
- `Message` - Chat messages (id, message_id, sender_id, conversation_id, content, created_at)

### `app/db.py` - Database Connection
- Creates async database engine
- `init_db()` - Creates tables if missing (preserves data)
- `reset_db()` - Drops and recreates tables (dev only)

### `app/schemas.py` - Data Validation
Pydantic models for request/response validation:
- `UserCreate`, `UserLogin`, `UserResponse`
- `Token`, `TokenRefresh`
- `ConversationCreate`, `MessageCreate`

### `app/auth.py` - Authentication
- JWT token creation/validation
- Password hashing (Argon2)
- `get_current_user()` - HTTP route dependency
- `get_current_user_websocket()` - WebSocket authentication

### `app/store_sql.py` - Database Operations
Async database operations:
- User CRUD operations
- Conversation management
- Message storage
- Membership checks

### `app/routes.py` - REST API Endpoints
Protected API routes:
- `GET /users` - List all users
- `GET /conversations` - List user's conversations
- `POST /conversations` - Create conversation (1-on-1 or group)
- `GET /conversations/{id}/messages` - Get messages
- `POST /messages` - Send message

### `app/auth_routes.py` - Authentication Endpoints
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### `app/websockets.py` - WebSocket Manager
Manages WebSocket connections:
- `ConnectionManager` - Tracks active connections per user
- `connect()` - Add connection
- `disconnect()` - Remove connection
- `broadcast_to_conversation()` - Send message to all members

### `app/main.py` - Application Entry Point
FastAPI application setup:
- Routes and middleware configuration
- WebSocket endpoint (`/ws`)
- Health checks (`/health`, `/ready`)
- Metrics endpoint (`/metrics`)
- Static file serving
- Observability setup (logging, tracing, rate limiting)

### `app/metrics.py` - Metrics Collection
Tracks application metrics:
- WebSocket connections (total, active)
- Messages sent (total, per second)
- Prometheus format export

### `app/logging_config.py` - Structured Logging
JSON-formatted logging configuration for production.

### `app/tracing.py` - OpenTelemetry Tracing
Request tracing setup for debugging and monitoring.

### `app/rate_limit.py` - Rate Limiting
Middleware for rate limiting:
- Per-user (authenticated) or per-IP (unauthenticated)
- Configurable limits (default: 60/min, 1000/hour)
- Exempt paths (health, metrics, docs)

---

## Frontend Files

### `static/index.html` - Login/Signup Page
- User registration and login
- Token storage in localStorage
- Redirects to chat interface

### `static/chat.html` - Main Chat Interface
- Displays conversations list
- Shows user list for starting 1-on-1 chats
- Group chat creation modal
- Real-time message display
- WebSocket connection management

---

## Workflow

### 1. User Registration/Login
1. User signs up via `POST /auth/signup`
2. Password is hashed with Argon2
3. User logs in via `POST /auth/login`
4. Receives JWT access and refresh tokens
5. Tokens stored in localStorage

### 2. Starting a Conversation

**1-on-1 Chat:**
1. User clicks on another user in the Users list
2. Frontend calls `POST /conversations` with other user's ID
3. Backend checks for existing 1-on-1 conversation
4. Returns existing or creates new conversation
5. Conversation appears in sidebar

**Group Chat:**
1. User clicks "+ New Group Chat"
2. Enters group name and participant usernames
3. Frontend resolves usernames to user IDs
4. Calls `POST /conversations` with member IDs
5. Backend creates group conversation (host automatically added)

### 3. Sending Messages

**Via HTTP:**
1. `POST /messages` with message content
2. Backend validates sender is conversation member
3. Message saved to database
4. Broadcasted via WebSocket to all members

**Via WebSocket:**
1. Client connects to `/ws?token=ACCESS_TOKEN`
2. Authenticates via token
3. Sends `{"type": "message", ...}` JSON
4. Backend validates and saves
5. Broadcasts to all conversation members

### 4. Real-time Updates
1. WebSocket connection established
2. Client joins conversation: `{"type": "join", "conversation_id": "..."}`
3. Messages broadcasted to all active connections
4. Frontend updates UI automatically
5. New conversations appear when messages received

---

## Key Concepts

### Authentication Flow
- JWT tokens in Authorization header: `Bearer <token>`
- WebSocket authentication via query param: `?token=<token>`
- Refresh tokens for long-lived sessions

### Conversation Types
- **1-on-1**: Exactly 2 members, shows other user's name
- **Group**: 3+ members, shows group title with 👥 icon

### Message Broadcasting
- Messages sent to all active WebSocket connections for conversation members
- Supports multiple devices per user
- Idempotent via `message_id` field

### Observability
- **Health Checks**: `/health` (always up), `/ready` (database check)
- **Metrics**: Prometheus format at `/metrics`
- **Logging**: Structured JSON logs
- **Tracing**: OpenTelemetry spans
- **Rate Limiting**: Per-user/IP limits with headers

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
2. **Security**: Set `SECRET_KEY` environment variable
3. **Logging**: JSON logs can be sent to log aggregation services
4. **Tracing**: Configure OTLP exporter for production
5. **Rate Limiting**: Consider Redis-backed limiter for multi-instance deployments
6. **CORS**: Update `allow_origins` in `main.py` for production
