# Quick Start Guide

Get up and running with Pneumatic Chat in 5 minutes!

## 🚀 Quick Start

### 1. Start the Server

```bash
# In project directory
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 2. Open the Web Interface

Visit `http://localhost:8000` in your browser.

The app will automatically serve the login page.

### 3. Create Your First Account

1. Click "Sign Up" tab
2. Enter:
   - **Username**: `alice`
   - **Password**: `password123`
   - **Full Name**: `Alice Smith` (optional)
3. Click "Create Account"
4. You'll automatically be logged in!

### 4. Start Chatting

#### Option A: 1-on-1 Chat
1. In the **Users** section, click on a user (e.g., "Bob")
2. A 1-on-1 conversation is created automatically
3. Start typing messages!

#### Option B: Group Chat
1. Click **"+ New Group Chat"** button
2. Enter a **Group Name** (e.g., "Team Chat")
3. Add participants by username (comma-separated, e.g., `bob, charlie`)
4. Click "Create Group"
5. Start chatting with the group!

### 5. Test with Multiple Users

**In another browser/incognito window:**
1. Visit `http://localhost:8000`
2. Sign up as `bob` / `password123`
3. Click on "alice" in the Users list
4. Send a message - Alice will see it appear automatically!

---

## 🎯 Common Tasks

### Task: Create a Group Chat

1. Click **"+ New Group Chat"**
2. Enter group name: `"Project Team"`
3. Add usernames: `bob, charlie, diana`
4. Click "Create Group"
5. All members can now chat together!

### Task: Use the API Programmatically

```python
import httpx

# Login
response = httpx.post("http://localhost:8000/auth/login", json={
    "username": "alice",
    "password": "password123"
})
token = response.json()["access_token"]

# Get current user info
response = httpx.get(
    "http://localhost:8000/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
user = response.json()

# List conversations
response = httpx.get(
    "http://localhost:8000/conversations",
    headers={"Authorization": f"Bearer {token}"}
)
conversations = response.json()["conversations"]

# Send a message
response = httpx.post(
    "http://localhost:8000/messages",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "message_id": "unique-id-123",
        "sender_id": user["id"],
        "conversation_id": conversations[0]["id"],
        "content": "Hello from API!"
    }
)
```

### Task: Connect via WebSocket

```javascript
// Get token first (from login)
const token = "YOUR_ACCESS_TOKEN";

// Connect
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

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
  console.log("Received:", data);
};
```

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

## 📚 Learn More

- **Full Guide**: See `USER_GUIDE.md` for comprehensive documentation
- **API Docs**: Visit http://localhost:8000/docs for interactive API documentation
- **Architecture**: See `ARCHITECTURE.md` for technical details

---

## 💡 Pro Tips

1. **1-on-1 vs Group**: Click users for 1-on-1, use "+ New Group Chat" for groups
2. **Multiple Devices**: You can be logged in from multiple devices simultaneously
3. **Auto Discovery**: New conversations appear automatically when someone messages you
4. **Rate Limits**: Default is 60 requests/minute per user/IP
5. **Logs**: Check server console for structured JSON logs

Happy chatting! 🚀
