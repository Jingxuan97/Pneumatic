# Pneumatic Chat - Architecture

## Tech Stack

### Core Framework
- **FastAPI** (0.95.2) - Modern Python web framework
  - Built on Starlette and Pydantic
  - Automatic OpenAPI/Swagger documentation
  - Native async/await support
  - WebSocket support

### Server & Deployment
- **Uvicorn** (0.22.0) - ASGI server
- **Gunicorn** (20.1.0) - Production process manager

### Database & ORM
- **SQLAlchemy** (1.4.46) - Async ORM
- **aiosqlite** (0.17.0) - SQLite driver (dev)
- **asyncpg** (0.27.0) - PostgreSQL driver (prod)

### Authentication & Security
- **PyJWT** (2.8.0) - JWT token handling
- **passlib[argon2]** (1.7.4) - Password hashing

### Observability
- **python-json-logger** (2.0.7) - Structured JSON logging
- **opentelemetry-api/sdk** (1.21.0) - Distributed tracing
- **opentelemetry-instrumentation-fastapi** (0.42b0) - FastAPI instrumentation

### Testing
- **pytest** (7.4.0) - Testing framework
- **pytest-asyncio** (0.21.1) - Async test support
- **httpx** (0.24.1) - HTTP client for tests

---

## Architecture Overview

### Project Structure

```
Pneumatic/
├── app/
│   ├── main.py              # FastAPI app, routes, WebSocket, observability
│   ├── routes.py            # REST API endpoints
│   ├── auth_routes.py       # Authentication endpoints
│   ├── auth.py              # JWT & password hashing
│   ├── websockets.py        # WebSocket connection manager
│   ├── store_sql.py         # Database operations
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── db.py                # Database connection
│   ├── metrics.py           # Prometheus metrics
│   ├── logging_config.py    # Structured logging
│   ├── tracing.py           # OpenTelemetry setup
│   └── rate_limit.py        # Rate limiting middleware
├── static/                  # Frontend files
│   ├── index.html           # Login/Signup
│   └── chat.html            # Chat interface
├── tests/                   # Test suite
└── requirements.txt         # Dependencies
```

---

## System Architecture

### Request Flow

```
Client Request
    ↓
Rate Limiting Middleware (per user/IP)
    ↓
CORS Middleware
    ↓
Authentication (JWT validation)
    ↓
Route Handler
    ↓
Database Operation (SQLAlchemy)
    ↓
Response
```

### WebSocket Flow

```
Client WebSocket Connection
    ↓
Token Authentication
    ↓
Connection Manager (track connection)
    ↓
Message Received
    ↓
Validation & Save to Database
    ↓
Broadcast to All Conversation Members
    ↓
All Active Connections Receive Message
```

---

## Database Schema

### Tables

**users**
- `id` (UUID, PK)
- `username` (String, unique)
- `full_name` (String, nullable)
- `password_hash` (String)

**conversations**
- `id` (UUID, PK)
- `title` (String)

**conversation_members**
- `conversation_id` (UUID, FK)
- `user_id` (UUID, FK)
- Primary key: (conversation_id, user_id)

**messages**
- `id` (UUID, PK)
- `message_id` (String, unique) - Client-supplied for idempotency
- `sender_id` (UUID, FK)
- `conversation_id` (UUID, FK)
- `content` (Text)
- `created_at` (DateTime)

---

## Observability Stack

### Health Checks
- **`/health`** - Basic health check (always returns 200)
- **`/ready`** - Readiness check (verifies database connectivity)
  - Returns 503 if database unavailable
  - Used by load balancers for health checks

### Metrics (Prometheus)
- **`/metrics`** - Prometheus-formatted metrics
  - `pneumatic_websocket_connections_total` - Total connections
  - `pneumatic_websocket_connections_active` - Current active connections
  - `pneumatic_messages_sent_total` - Total messages sent
  - `pneumatic_messages_per_second` - Average messages/sec (60s window)

### Structured Logging
- JSON-formatted logs to stdout
- Includes: timestamp, level, logger, message, module, function, line
- Supports extra fields for context

### Distributed Tracing
- OpenTelemetry instrumentation
- Automatic span creation for HTTP requests
- Console exporter (can be configured for OTLP in production)

### Rate Limiting
- Token bucket algorithm
- Per-user (authenticated) or per-IP (unauthenticated)
- Default: 60 requests/minute, 1000 requests/hour
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Exempt paths: `/health`, `/ready`, `/metrics`, `/docs`

---

## Security Features

### Authentication
- JWT access tokens (30 min expiry)
- JWT refresh tokens (7 day expiry)
- Token type validation
- Secure token encoding with secret key

### Password Security
- Argon2 password hashing
- Passwords never stored in plain text
- Secure password verification

### WebSocket Security
- Token-based authentication
- User ID extraction from token
- Conversation membership validation

### Rate Limiting
- Prevents abuse and DoS attacks
- Per-user/IP limits
- Configurable thresholds

---

## Frontend Architecture

### Pages

**index.html** - Login/Signup
- User registration
- Login with token storage
- Token validation on page load
- Redirects to chat interface

**chat.html** - Main Interface
- Sidebar with conversations and users
- Main chat area with messages
- WebSocket connection management
- Real-time message updates
- Group chat creation modal

### Key Features
- **1-on-1 Conversations**: Click user → auto-create conversation
- **Group Chats**: "+ New Group Chat" → add participants
- **Auto Discovery**: New conversations appear when messages received
- **Multiple Devices**: Support for simultaneous connections

---

## Deployment Considerations

### Development
- SQLite database (file-based)
- Console logging
- Console tracing exporter
- In-memory rate limiting

### Production
- PostgreSQL database (set `DATABASE_URL`)
- Structured JSON logs → log aggregation service
- OTLP tracing exporter → tracing backend
- Redis-backed rate limiting (for multi-instance)
- Set `SECRET_KEY` environment variable
- Configure CORS `allow_origins`
- Use Gunicorn with Uvicorn workers

### Scaling
- Stateless application (can run multiple instances)
- Database connection pooling
- WebSocket connections per instance
- Consider Redis pub/sub for cross-instance messaging (if needed)

---

## API Endpoints

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Conversations
- `GET /conversations` - List user's conversations
- `POST /conversations` - Create conversation (1-on-1 or group)
- `GET /conversations/{id}/messages` - Get messages

### Messages
- `POST /messages` - Send message via HTTP

### Users
- `GET /users` - List all users

### Observability
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /metrics` - Prometheus metrics

### WebSocket
- `WS /ws?token=TOKEN` - WebSocket connection

---

## Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **WebSocket Tests**: Real-time messaging tests
- **Authentication Tests**: Token validation tests

Run with: `pytest`
