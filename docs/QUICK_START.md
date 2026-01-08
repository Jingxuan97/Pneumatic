# Quick Start Guide

Get up and running with Pneumatic Chat in 5 minutes!

## 🚀 Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required: Generate a secure secret key (minimum 32 characters)
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Optional: Use PostgreSQL (defaults to SQLite for dev)
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"
```

### 3. Start the Server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 4. Create Your First Account

1. Visit `http://localhost:8000`
2. Click "Sign Up" tab
3. Enter:
   - **Username**: `alice`
   - **Password**: `password123`
   - **Full Name**: `Alice Smith` (optional)
4. Click "Create Account"
5. You'll automatically be logged in!

### 5. Start Chatting

#### 1-on-1 Chat
1. In the **Users** section, click on a user
2. A conversation is created automatically
3. Start typing messages!

#### Group Chat
1. Click **"+ New Group Chat"** button
2. Enter a **Group Name** (e.g., "Team Chat")
3. Add participants by username (comma-separated, e.g., `bob, charlie`)
4. Click "Create Group"
5. Start chatting!

### 6. Test with Multiple Users

**In another browser/incognito window:**
1. Visit `http://localhost:8000`
2. Sign up as `bob` / `password123`
3. Click on "alice" in the Users list
4. Send a message - Alice will see it appear automatically!

---

## 📊 Observability Endpoints

### Health Check
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

### Readiness Check
```bash
curl http://localhost:8000/ready
# Returns: {"status": "ready"} or 503 if database unavailable
```

### Metrics (Prometheus Format)
```bash
curl http://localhost:8000/metrics
# Returns Prometheus-formatted metrics:
# - pneumatic_websocket_connections_total
# - pneumatic_websocket_connections_active
# - pneumatic_messages_sent_total
# - pneumatic_messages_per_second
```

---

## 🎯 Quick API Examples

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

### Get Conversations
```bash
curl -X GET "http://localhost:8000/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Send Message
```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "unique-id-123",
    "sender_id": "your-user-id",
    "conversation_id": "conv-id",
    "content": "Hello!"
  }'
```

---

## 💡 Pro Tips

1. **1-on-1 vs Group**: Click users for 1-on-1, use "+ New Group Chat" for groups
2. **Multiple Devices**: You can be logged in from multiple devices simultaneously
3. **Auto Discovery**: New conversations appear automatically when someone messages you
4. **Rate Limits**: Default is 60 requests/minute per user/IP
5. **API Docs**: Visit `http://localhost:8000/docs` for interactive API documentation

---

## 📚 Next Steps

- **Tutorial**: See `TUTORIAL.md` for comprehensive feature guide
- **Deployment**: See `DEPLOYMENT.md` for production deployment
- **Debugging**: See `DEBUG.md` for troubleshooting

Happy chatting! 🚀
