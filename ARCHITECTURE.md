# Pneumatic Chat Application - Tech Stack & Architecture

## 📚 Tech Stack Overview

### Core Framework

- **FastAPI** (0.95.2) - Modern, fast web framework for building APIs with Python
  - Built on Starlette and Pydantic
  - Automatic OpenAPI/Swagger documentation
  - Native async/await support
  - WebSocket support out of the box

### Server & Deployment

- **Uvicorn** (0.22.0) - ASGI server for running FastAPI
  - High-performance async server
  - Hot reload support for development
- **Gunicorn** (20.1.0) - Production WSGI/ASGI server
  - Process manager for running multiple worker processes

### Database & ORM

- **SQLAlchemy** (1.4.46) - Python SQL toolkit and ORM
  - Async support via `sqlalchemy.ext.asyncio`
  - Declarative base for model definitions
  - Database-agnostic (works with SQLite, PostgreSQL, etc.)

### Database Drivers

- **aiosqlite** (0.17.0) - Async SQLite driver for development
- **asyncpg** (0.27.0) - Fast async PostgreSQL driver for production

### Data Validation

- **Pydantic** (1.10) - Data validation using Python type annotations
  - Used for request/response schemas
  - Automatic validation and serialization

### Testing

- **pytest** (7.4.0) - Testing framework
- **httpx** (0.24.1) - Async HTTP client (used by FastAPI TestClient)

---

## 🏗️ Architecture Overview

### Project Structure

```
Pneumatic/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI app & WebSocket endpoint
│   ├── routes.py          # REST API endpoints
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── store_sql.py       # Async database operations (SQLStore)
│   ├── store.py           # In-memory store (unused, legacy)
│   ├── websockets.py      # WebSocket connection manager
│   └── db.py              # Database connection setup
├── tests/                 # Test suite
├── client.html            # Simple HTML WebSocket client
├── main.py                # Entry point (imports app.main)
└── requirements.txt       # Python dependencies
```

---

## 🔄 Data Flow & Components

### 1. **Database Layer** (`app/models.py`, `app/db.py`)

**Models (SQLAlchemy ORM):**

- `User` - User accounts with unique usernames
- `Conversation` - Chat rooms/groups
- `ConversationMember` - Many-to-many relationship (users ↔ conversations)
- `Message` - Individual chat messages with:
  - `message_id` (client-supplied UUID for idempotency)
  - `sender_id`, `conversation_id`, `content`
  - `created_at` timestamp

**Database Setup:**

- Uses async SQLAlchemy engine
- Supports SQLite (dev) and PostgreSQL (production)
- Auto-creates tables on startup (dev mode)
- Connection pooling handled by SQLAlchemy

### 2. **Data Access Layer** (`app/store_sql.py`)

**SQLStore Class** - Async database operations:

- `create_user(username)` - Create new user
- `get_user(user_id)` - Retrieve user by ID
- `create_conversation(title, member_ids)` - Create conversation with members
- `get_conversation(conv_id)` - Get conversation with member list
- `save_message(message_payload)` - Save message (with idempotency check)
- `list_messages(conv_id, limit)` - Fetch messages for a conversation

**Key Features:**

- All methods are async
- Proper session management with context managers
- Idempotency: duplicate `message_id` returns existing message
- Validation: checks user exists, conversation exists, sender is member

### 3. **API Layer** (`app/routes.py`)

**REST Endpoints:**

- `POST /users` - Create user
- `POST /conversations` - Create conversation
- `GET /conversations/{conv_id}/messages` - List messages
- `POST /messages` - Send message via HTTP (also broadcasts via WebSocket)

**Request/Response Schemas** (`app/schemas.py`):

- `UserCreate` - Username input
- `ConversationCreate` - Title + member IDs
- `MessageCreate` - Message data (message_id, sender_id, conversation_id, content)
- `Message` - Full message with timestamps

### 4. **WebSocket Layer** (`app/websockets.py`, `app/main.py`)

**ConnectionManager Class:**

- Manages active WebSocket connections
- Supports **multiple connections per user** (multiple devices)
- Thread-safe with `asyncio.Lock()`

**Key Methods:**

- `connect(user_id, websocket)` - Register new connection
- `disconnect(user_id, websocket)` - Remove specific connection
- `send_personal(user_id, data)` - Send to all user's connections
- `broadcast_to_conversation(conv_id, data)` - Send to all members

**WebSocket Endpoint** (`/ws/{user_id}`):

1. Validates user exists
2. Accepts connection
3. Listens for messages:
   - `{"type": "join", "conversation_id": "..."}` - Join conversation
   - `{"type": "message", ...}` - Send message
4. Saves message to database
5. Broadcasts to all conversation members
6. Handles disconnects gracefully

---

## 🔀 Request Flow Examples

### Example 1: HTTP Message Flow

```
Client → POST /messages
  ↓
routes.py: post_message()
  ↓
store_sql.py: save_message()
  ↓ (validates conversation, membership)
  ↓ (saves to database)
  ↓
routes.py: manager.broadcast_to_conversation()
  ↓
websockets.py: broadcast_to_conversation()
  ↓ (loads conversation members)
  ↓ (sends to all active WebSocket connections)
```

### Example 2: WebSocket Message Flow

```
Client → WebSocket: {"type": "message", ...}
  ↓
main.py: websocket_endpoint()
  ↓
store_sql.py: save_message()
  ↓ (saves to database)
  ↓
websockets.py: broadcast_to_conversation()
  ↓ (sends to all conversation members)
```

### Example 3: Multiple Devices

```
User "alice" connects from:
  - Phone (WebSocket 1)
  - Laptop (WebSocket 2)
  - Tablet (WebSocket 3)

When bob sends a message:
  → broadcast_to_conversation() finds alice in members
  → Sends to all 3 of alice's WebSocket connections
  → All devices receive the message simultaneously
```

---

## 🎯 Design Patterns & Features

### 1. **Idempotency**

- Client-supplied `message_id` prevents duplicate messages
- If duplicate detected, returns existing message instead of error

### 2. **Async/Await Throughout**

- All database operations are async
- WebSocket operations are async
- Enables high concurrency

### 3. **Connection Management**

- Thread-safe connection tracking
- Automatic cleanup on disconnect
- Supports multiple devices per user

### 4. **Validation Layers**

- Pydantic schemas validate request data
- Database constraints enforce data integrity
- Business logic validates permissions (membership checks)

### 5. **Error Handling**

- HTTP endpoints return proper status codes (400, 403, 404)
- WebSocket sends error messages as JSON
- Graceful disconnect handling

---

## 🔧 Configuration

### Database

- **Development**: SQLite (`sqlite+aiosqlite:///./dev.db`)
- **Production**: PostgreSQL (`postgresql+asyncpg://...`)
- Set via `DATABASE_URL` environment variable

### Startup Behavior

- Dev mode: Auto-drops and recreates tables (for clean testing)
- Production: Should use migrations instead

---

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests
pytest tests/test_app.py
```

---

## 📝 Key Concepts

### Why Async?

- Handles many concurrent connections efficiently
- Database I/O doesn't block other requests
- WebSocket connections are naturally async

### Why SQLAlchemy?

- Database-agnostic (easy to switch from SQLite to PostgreSQL)
- Type-safe model definitions
- Relationship management (users ↔ conversations)

### Why Pydantic?

- Automatic request validation
- Type hints for better IDE support
- Automatic OpenAPI schema generation

### Why Multiple Connections Per User?

- Users have multiple devices (phone, laptop, tablet)
- All devices should receive messages in real-time
- Better user experience

---

## 🔍 Current Limitations & Future Improvements

1. **No Authentication** - Anyone can connect as any user_id
2. **No CORS** - Frontend may have cross-origin issues
3. **No Rate Limiting** - Vulnerable to abuse
4. **Limited Pagination** - Only limit, no cursor-based pagination
5. **Outdated Dependencies** - FastAPI 0.95.2 (current is 0.115+)
6. **No Message History** - Can't fetch messages before a certain point
7. **No Typing Indicators** - No "user is typing" feature
8. **No Read Receipts** - No message read status
