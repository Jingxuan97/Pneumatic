# Pneumatic Chat - Secure Real-Time Messaging

A production-ready real-time chat application with JWT authentication, WebSocket messaging, and Redis pub/sub for horizontal scaling.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
uvicorn main:app --reload
```

Server runs at: `http://localhost:8000`

### 3. Use the Application
- **Web UI**: Open `index.html` in your browser
- **API Docs**: http://localhost:8000/docs
- **Quick Start Guide**: See `QUICK_START.md`

## 📖 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[User Guide](USER_GUIDE.md)** - Complete feature documentation
- **[Architecture](ARCHITECTURE.md)** - Technical architecture overview
- **[Authentication](AUTHENTICATION.md)** - Auth implementation details
- **[Redis Setup](REDIS_SETUP.md)** - Redis pub/sub configuration
- **[Testing Guide](TESTING_GUIDE.md)** - How to test features

## ✨ Features

### Core Features
- ✅ **JWT Authentication** - Secure token-based auth with refresh tokens
- ✅ **Real-time Messaging** - WebSocket-based instant messaging
- ✅ **Multiple Conversations** - Create and manage multiple chat rooms
- ✅ **Secure Passwords** - Argon2 password hashing
- ✅ **Modern UI/UX** - Beautiful, responsive web interface

### Advanced Features
- ✅ **Redis Pub/Sub** - Horizontal scaling across multiple server instances
- ✅ **Presence Tracking** - Know who's online with TTL-based tracking
- ✅ **Message Idempotency** - Prevent duplicate messages
- ✅ **Multiple Devices** - Connect from phone, laptop, tablet simultaneously
- ✅ **Permission Checks** - Conversation membership validation

## 🧪 Testing

```bash
# Run all tests
python -m pytest -q

# Test Redis connection
python test_redis_connection.py

# Test multi-instance flow
python test_multi_instance.py

# Run examples
python examples/redis_example.py
```

## 📁 Project Structure

```
Pneumatic/
├── app/                    # Application code
│   ├── main.py            # FastAPI app & WebSocket
│   ├── routes.py          # REST API endpoints
│   ├── auth_routes.py     # Authentication endpoints
│   ├── auth.py            # JWT & password hashing
│   ├── websockets.py      # WebSocket connection manager
│   ├── pubsub.py          # Redis pub/sub adapter
│   ├── store_sql.py       # Database operations
│   ├── models.py          # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── tests/                 # Test suite
├── examples/              # Code examples
├── index.html            # Login/Signup page
├── chat.html             # Main chat interface
└── requirements.txt      # Dependencies
```

## 🔧 Configuration

### Environment Variables

```bash
# Database (optional)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/dbname"

# Redis (optional - for multi-instance)
export REDIS_URL="redis://localhost:6379/0"

# Security (required in production)
export SECRET_KEY="your-very-secure-secret-key-minimum-32-characters"

# Presence TTL (optional)
export PRESENCE_TTL_SECONDS="300"  # 5 minutes default
```

## 🎯 Use Cases

1. **Team Chat** - Internal team communication
2. **Customer Support** - Real-time support chat
3. **Social Platform** - User-to-user messaging
4. **Learning** - Study pub/sub patterns, WebSockets, JWT auth

## 📚 Learning Resources

- **Complete Examples**: `examples/complete_chat_example.py`
- **Redis Examples**: `examples/redis_example.py`
- **API Reference**: See `USER_GUIDE.md` for full API docs

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM
- **WebSockets** - Real-time communication
- **Redis** - Pub/sub messaging (optional)
- **JWT** - Token-based authentication
- **Argon2** - Secure password hashing

## 📝 License

This is a learning/example project.
