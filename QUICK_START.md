# Quick Start Guide

Get up and running with Pneumatic Chat in 5 minutes!

## 🚀 Quick Start

### 1. Start the Server

```bash
# In project directory
uvicorn main:app --reload
```

Server runs at: `http://localhost:8000`

### 2. Open the Web Interface

Open `index.html` in your browser, or visit:
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 3. Create Your First Account

1. Click "Sign Up" tab
2. Enter username: `alice`
3. Enter password: `password123`
4. Click "Create Account"

### 4. Login

1. Click "Login" tab (or it switches automatically)
2. Enter same credentials
3. Click "Login"
4. You'll be redirected to the chat page!

### 5. Create a Conversation

1. Click "+ New Conversation"
2. Enter title: "My First Chat"
3. Click "Create"
4. Conversation appears in sidebar

### 6. Send a Message

1. Select the conversation
2. Type a message in the input box
3. Press Enter or click "Send"
4. Message appears instantly!

---

## 🎯 Common Tasks

### Task: Chat with Another User

**Step 1:** Create second user (in another browser/incognito)
- Sign up as `bob` / `password123`

**Step 2:** Get Bob's user ID
- Login as bob
- Check browser console or use API:
  ```bash
  curl -X GET "http://localhost:8000/auth/me" \
    -H "Authorization: Bearer BOB_TOKEN"
  ```

**Step 3:** Alice creates conversation with Bob
- Alice clicks "+ New Conversation"
- Enter Bob's user ID in member field
- Create conversation

**Step 4:** Both join and chat!
- Both users select the conversation
- Messages appear in real-time

### Task: Use the API Programmatically

```python
import httpx

# Login
response = httpx.post("http://localhost:8000/auth/login", json={
    "username": "alice",
    "password": "password123"
})
token = response.json()["access_token"]

# Create conversation
response = httpx.post(
    "http://localhost:8000/conversations",
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "API Chat", "member_ids": []}
)
conv_id = response.json()["id"]

# Send message
httpx.post(
    "http://localhost:8000/messages",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "message_id": "unique-id",
        "sender_id": "your-user-id",
        "conversation_id": conv_id,
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

## 📚 Learn More

- **Full Guide**: See `USER_GUIDE.md` for comprehensive documentation
- **Examples**: Run `python examples/complete_chat_example.py` for code examples
- **API Docs**: Visit http://localhost:8000/docs for interactive API documentation
- **Architecture**: See `ARCHITECTURE.md` for technical details

---

## 🎓 Learning Path

1. **Start Simple**: Use the web UI (`index.html`)
2. **Try API**: Use curl or Postman to test endpoints
3. **Build Client**: Create your own client using WebSocket API
4. **Explore**: Check out the code examples in `examples/`

---

## 💡 Pro Tips

1. **Keep tokens safe** - Store in localStorage or secure storage
2. **Handle disconnects** - Implement WebSocket reconnection
3. **Unique message IDs** - Always use `crypto.randomUUID()` or similar
4. **Check membership** - Verify user is in conversation before sending
5. **Use API docs** - `/docs` endpoint has interactive testing

Happy coding! 🚀
