# Codebase Explanation - Simplified

## Tech Stack Overview

### Core Technologies
1. **FastAPI** - Modern Python web framework for building APIs
2. **SQLAlchemy** - ORM (Object-Relational Mapping) for database operations
3. **SQLite** - Lightweight database (dev) / PostgreSQL (production)
4. **WebSockets** - Real-time bidirectional communication
5. **JWT (JSON Web Tokens)** - Token-based authentication
6. **Argon2** - Secure password hashing
7. **Pydantic** - Data validation and serialization


---

## File-by-File Breakdown

### 1. `app/models.py` - Database Models
**Purpose**: Defines the database schema using SQLAlchemy ORM.

**What it does**:
- `User`: Stores user accounts (id, username, full_name, password_hash)
- `Conversation`: Chat rooms/groups (id, title)
- `ConversationMember`: Links users to conversations (many-to-many relationship)
- `Message`: Individual chat messages (id, message_id, sender_id, conversation_id, content, created_at)

**Key concept**: These are Python classes that map to database tables. SQLAlchemy handles SQL generation.

---

### 2. `app/db.py` - Database Connection
**Purpose**: Sets up database connection and creates tables.

**What it does**:
- Creates async database engine (SQLite for dev, PostgreSQL for prod)
- `init_db()`: Creates tables if they don't exist (preserves data)
- `reset_db()`: Drops and recreates tables (dev only)

**Key concept**: Database connection pool that handles async operations.

---

### 3. `app/schemas.py` - Data Validation
**Purpose**: Pydantic models for request/response validation.

**What it does**:
- Validates incoming data (e.g., signup form, message content)
- Ensures data types and required fields are correct
- Converts between Python dicts and JSON

**Key concept**: Type safety and validation before processing requests.

---

### 4. `app/store_sql.py` - Database Operations
**Purpose**: All database read/write operations.

**What it does**:
- `create_user()`: Register new user
- `get_user()`: Get user by ID
- `get_user_by_username()`: Get user for login (includes password hash)
- `list_all_users()`: Get all registered users
- `create_conversation()`: Create new chat room
- `get_conversation()`: Get conversation details
- `list_user_conversations()`: Get all conversations for a user
- `save_message()`: Save message to database
- `list_messages()`: Get messages from a conversation
- `find_one_on_one_conversation()`: Check if 1-on-1 chat already exists

**Key concept**: Abstraction layer - routes call these methods instead of writing SQL directly.

---

### 5. `app/auth.py` - Authentication Logic
**Purpose**: Handles password hashing, JWT token creation/validation.

**What it does**:
- `verify_password()`: Check if password matches hash
- `get_password_hash()`: Hash password with Argon2
- `create_access_token()`: Generate JWT token (30 min expiry)
- `create_refresh_token()`: Generate refresh token (7 days expiry)
- `decode_token()`: Validate and decode JWT
- `get_current_user()`: Extract user from HTTP request token
- `get_current_user_websocket()`: Extract user from WebSocket token

**Key concept**: JWT tokens contain user ID. Server validates token to identify user.

---

### 6. `app/auth_routes.py` - Authentication Endpoints
**Purpose**: HTTP endpoints for signup, login, token refresh.

**What it does**:
- `POST /auth/signup`: Create new account
- `POST /auth/login`: Get JWT tokens (returns access + refresh tokens)
- `POST /auth/refresh`: Get new tokens using refresh token
- `GET /auth/me`: Get current user info

**Key concept**: These endpoints don't require authentication (except `/auth/me`).

---

### 7. `app/routes.py` - Main API Endpoints
**Purpose**: HTTP endpoints for conversations and messages.

**What it does**:
- `GET /users`: List all users (requires auth)
- `GET /conversations`: List user's conversations (requires auth)
- `POST /conversations`: Create conversation (requires auth)
- `GET /conversations/{id}/messages`: Get messages (requires auth + membership)
- `POST /messages`: Send message via HTTP (requires auth)

**Key concept**: All routes use `Depends(get_current_user)` to require authentication.

---

### 8. `app/websockets.py` - WebSocket Connection Manager
**Purpose**: Manages real-time WebSocket connections.

**What it does**:
- `ConnectionManager`: Tracks active WebSocket connections
  - `connect()`: Add new WebSocket connection
  - `disconnect()`: Remove connection
  - `broadcast_to_conversation()`: Send message to all members
- Supports multiple connections per user (multiple browser tabs)

**Key concept**: Maintains a dictionary of active connections: `{user_id: [websocket1, websocket2, ...]}`

---

---

### 10. `app/main.py` - Application Entry Point
**Purpose**: FastAPI app setup, WebSocket endpoint, startup/shutdown.

**What it does**:
- Creates FastAPI app
- Adds CORS middleware (allows frontend to connect)
- Includes routers (auth_routes, routes)
- `@app.on_event("startup")`: Initialize database
- `@app.websocket("/ws")`: WebSocket endpoint
  - Authenticates user via token
  - Handles `join` and `message` events
  - Broadcasts messages to conversation members

**Key concept**: This is where everything comes together.

---

### 11. `app/store.py` - In-Memory Store (Unused)
**Purpose**: Old in-memory implementation (not used anymore).

**Status**: Can be deleted - we use `store_sql.py` instead.

---

## Request Flow Examples

### 1. User Signs Up
```
Frontend → POST /auth/signup {username, password, full_name}
  ↓
auth_routes.py:signup()
  ↓
auth.py:get_password_hash() → Hash password
  ↓
store_sql.py:create_user() → Save to database
  ↓
Return UserResponse {id, username, full_name}
```

### 2. User Logs In
```
Frontend → POST /auth/login {username, password}
  ↓
auth_routes.py:login()
  ↓
store_sql.py:get_user_by_username() → Get user + password_hash
  ↓
auth.py:verify_password() → Check password
  ↓
auth.py:create_access_token() + create_refresh_token() → Generate JWTs
  ↓
Return Token {access_token, refresh_token}
```

### 3. User Sends Message via WebSocket
```
Frontend → WebSocket.send({type: "message", conversation_id, content, message_id})
  ↓
main.py:websocket_endpoint() → Receives message
  ↓
auth.py:get_current_user_websocket() → Validate token, get user_id
  ↓
store_sql.py:save_message() → Save to database
  ↓
websockets.py:manager.broadcast_to_conversation() → Send to all members
  ↓
All connected clients receive message
```

### 4. User Creates Conversation
```
Frontend → POST /conversations {title, member_ids: [other_user_id]}
  ↓
routes.py:create_conversation()
  ↓
auth.py:get_current_user() → Validate token, get current_user
  ↓
store_sql.py:find_one_on_one_conversation() → Check if exists (for 1-on-1)
  ↓
store_sql.py:create_conversation() → Create in database
  ↓
Return Conversation {id, title, members}
```

---

## Data Flow: Message Broadcasting

```
User A sends message
  ↓
WebSocket receives message
  ↓
Save to database
  ↓
ConnectionManager.broadcast_to_conversation()
  ↓
For each member in conversation:
  - Get their active WebSocket connections
  - Send message to each connection
```

---

## Key Concepts Explained

### 1. JWT Authentication
- **Token**: Encrypted string containing user ID and expiry time
- **Flow**: Login → Get token → Include in requests → Server validates → Extract user ID
- **Why**: Stateless authentication (no server-side sessions)

### 2. WebSockets vs HTTP
- **HTTP**: Request → Response (one-way, client initiates)
- **WebSocket**: Persistent connection (two-way, server can push)
- **Use case**: Real-time chat needs WebSockets

### 3. Database Relationships
- **User** ↔ **ConversationMember** ↔ **Conversation**: Many-to-many (users can be in multiple conversations)
- **Message** → **Conversation**: One-to-many (conversation has many messages)
- **Message** → **User**: Many-to-one (user sends many messages)

### 4. Async/Await
- **Why**: Handle multiple connections simultaneously
- **How**: `async def` functions can wait for I/O (database, network) without blocking

---

## Simplification Opportunities

### Can Remove (Non-Essential):
1. **Refresh tokens** - Can simplify to just access tokens
2. **Full name field** - Can use just username
3. **1-on-1 deduplication** - Optimization, not core feature
4. **Multiple connections per user** - Can simplify to one per user

### Core Features (Keep):
1. User signup/login
2. JWT authentication
3. Conversation creation
4. Message sending/receiving
5. WebSocket real-time communication
6. Database persistence

---

## Next Steps

Would you like me to create a simplified version that removes the non-essential features?
