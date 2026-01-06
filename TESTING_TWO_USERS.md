# Testing with Two Users

This guide explains how to test the chat application with two users simultaneously.

## Method 1: Two Browser Windows (Recommended)

### Step 1: Start the Server
```bash
uvicorn app.main:app --reload
```

### Step 2: Create First User
1. Open your browser and go to `http://localhost:8000` (or open `index.html` directly)
2. Click on the **Sign Up** tab
3. Fill in the form:
   - **Full Name**: Alice Smith
   - **Username**: alice
   - **Password**: password123
4. Click **Create Account**
5. You'll be redirected to the login page - log in with:
   - **Username**: alice
   - **Password**: password123
6. You'll be taken to the chat page

### Step 3: Create Second User (New Window)
1. Open a **new browser window** (or a different browser entirely)
2. Go to `http://localhost:8000` (or open `index.html`)
3. Click on the **Sign Up** tab
4. Fill in the form:
   - **Full Name**: Bob Johnson
   - **Username**: bob
   - **Password**: password123
5. Click **Create Account** and log in

### Step 4: Test Chat Between Users

**In Alice's window:**
1. You should see "Bob Johnson" in the **Users** section
2. Click on **Bob Johnson** to start a conversation
3. Type a message and press Enter or click Send

**In Bob's window:**
1. You should see "Alice Smith" in the **Users** section
2. The conversation with Alice should appear in the **Conversations** list
3. Click on the conversation to see Alice's message
4. Reply to Alice's message

## Method 2: Incognito/Private Window

1. Open one window in **normal mode** - create and log in as Alice
2. Open another window in **incognito/private mode** - create and log in as Bob
3. Follow the same steps as Method 1

## Method 3: Different Browsers

1. Use **Chrome** for one user (e.g., Alice)
2. Use **Firefox** or **Safari** for the other user (e.g., Bob)
3. Each browser maintains separate localStorage, so you can have different sessions

## Quick Test Checklist

- [ ] Create two user accounts (Alice and Bob)
- [ ] Both users can see each other in the Users list
- [ ] Alice can click on Bob to start a conversation
- [ ] Bob receives the conversation in their Conversations list
- [ ] Messages sent by Alice appear in Bob's chat
- [ ] Messages sent by Bob appear in Alice's chat
- [ ] Full names are displayed correctly
- [ ] WebSocket connections work (real-time messaging)

## Troubleshooting

### "I can only see myself in the Users list"
- Make sure both users are logged in
- Refresh both browser windows
- Check that both accounts were created successfully

### "Messages aren't appearing in real-time"
- Check the browser console for WebSocket errors
- Make sure both users have joined the conversation (click on it)
- Verify the server is running and WebSocket endpoint is accessible

### "I can't log in as the second user"
- Use a different browser window (not just a new tab)
- Or use incognito/private mode
- Or click "Switch Account" on the login page to clear the first session

### "Database was reset"
- The database should now persist between server restarts
- If you see this, check that `app/db.py` and `app/main.py` have the latest changes
- Your accounts should still be there after restarting the server

## Testing Multi-User Scenarios

### Test 1: One-on-One Chat
- Alice and Bob have a private conversation
- Messages only appear to each other

### Test 2: Group Conversation
- Alice creates a new conversation
- Add Bob as a member (using the "New Conversation" modal)
- Both users can see and send messages

### Test 3: Multiple Conversations
- Alice starts a conversation with Bob
- Bob starts a conversation with Alice
- Both conversations should appear in each user's list

### Test 4: Presence (if Redis is running)
- When a user is online, they appear in the Users list
- When they disconnect, they may show as offline (depending on implementation)

## Tips

1. **Keep both windows visible** - Use side-by-side windows to see messages appear in real-time
2. **Use different full names** - Makes it easier to identify which user is which
3. **Test with different browsers** - Chrome and Firefox work well together
4. **Check the server logs** - Watch for WebSocket connection messages and errors
5. **Test logout/login** - Make sure you can switch between accounts easily

## Example Test Flow

```
Window 1 (Alice):
1. Sign up: Alice Smith / alice / password123
2. Log in
3. See Bob in Users list
4. Click on Bob → Conversation created
5. Send: "Hi Bob!"
6. See Bob's reply: "Hi Alice!"

Window 2 (Bob):
1. Sign up: Bob Johnson / bob / password123
2. Log in
3. See Alice in Users list
4. See conversation with Alice appear automatically
5. Click conversation
6. See Alice's message: "Hi Bob!"
7. Send: "Hi Alice!"
```

Happy testing! 🚀
