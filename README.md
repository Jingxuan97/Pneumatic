# Pneumatic Chat - Production-Ready Real-Time Messaging

A production-ready real-time chat application with JWT authentication, WebSocket messaging, and full observability.

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key-minimum-32-characters"
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"  # or PostgreSQL for production

# Start server
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### Production Deployment

- **[Quick EB Deployment](docs/EB_DEPLOYMENT.md)** - Clean, step-by-step EB deployment
- **[Complete AWS Guide](docs/AWS_DEPLOYMENT_GUIDE.md)** - Full guide with RDS and domain setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## ✨ Features

### Core Features
- ✅ **JWT Authentication** - Secure token-based auth with refresh tokens
- ✅ **Real-time Messaging** - WebSocket-based instant messaging
- ✅ **1-on-1 & Group Chats** - Private conversations and group conversations
- ✅ **Secure Passwords** - Argon2 password hashing
- ✅ **Modern UI/UX** - Beautiful, responsive web interface
- ✅ **Multiple Devices** - Connect from multiple devices simultaneously

### Production Features
- ✅ **Health Checks** - `/health` and `/ready` endpoints for load balancers
- ✅ **Prometheus Metrics** - `/metrics` endpoint with connection and message stats
- ✅ **Structured Logging** - JSON-formatted logs for production
- ✅ **OpenTelemetry Tracing** - Request tracing for debugging
- ✅ **Rate Limiting** - Per-user/IP rate limiting (60/min, 1000/hour)

## 📖 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[User Guide](docs/USER_GUIDE.md)** - Complete feature documentation
- **[Architecture](docs/ARCHITECTURE.md)** - Technical architecture overview
- **[Authentication](docs/AUTHENTICATION.md)** - Auth implementation details
- **[Complete AWS Deployment Guide](docs/AWS_DEPLOYMENT_GUIDE.md)** - Step-by-step deployment with database and domain setup
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Quick reference for AWS Elastic Beanstalk
- **[Codebase Explanation](docs/CODEBASE_EXPLANATION.md)** - Code understanding guide

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

## 📁 Project Structure

```
Pneumatic/
├── app/                    # Application code
│   ├── main.py            # FastAPI app, WebSocket, health/metrics
│   ├── routes.py          # REST API endpoints
│   ├── auth_routes.py     # Authentication endpoints
│   ├── auth.py            # JWT & password hashing
│   ├── websockets.py      # WebSocket connection manager
│   ├── store_sql.py       # Database operations
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── metrics.py         # Prometheus metrics
│   ├── logging_config.py  # Structured JSON logging
│   ├── tracing.py         # OpenTelemetry tracing
│   └── rate_limit.py      # Rate limiting middleware
├── static/                # Frontend files
│   ├── index.html         # Login/Signup page
│   └── chat.html          # Main chat interface
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .ebextensions/         # Elastic Beanstalk configuration
├── requirements.txt       # Dependencies
├── Procfile              # Production process definition
└── pytest.ini            # Pytest configuration
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Security (required)
SECRET_KEY="your-very-secure-secret-key-minimum-32-characters"

# Database (required)
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
```

### Optional Environment Variables

```bash
# CORS (default: "*")
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Rate Limiting (default: 60/min, 1000/hour)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM
- **WebSockets** - Real-time communication
- **JWT** - Token-based authentication
- **Argon2** - Secure password hashing
- **Prometheus** - Metrics format
- **OpenTelemetry** - Distributed tracing
- **Gunicorn** - Production WSGI server

## 🎯 Use Cases

1. **Team Chat** - Internal team communication
2. **Customer Support** - Real-time support chat
3. **Social Platform** - User-to-user messaging
4. **Learning** - Study WebSockets, JWT auth, observability

## 📝 License

This is a learning/example project.
