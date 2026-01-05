# Authentication & Security Implementation

## Overview

The application now implements JWT-based authentication with secure password hashing and protected WebSocket connections.

## Features Implemented

### 1. **Password Security**
- **Argon2** password hashing via `passlib`
- Passwords are never stored in plain text
- Secure password verification

### 2. **JWT Tokens**
- **Access Tokens**: Short-lived (30 minutes) for API access
- **Refresh Tokens**: Long-lived (7 days) for token renewal
- Token type validation (access vs refresh)
- Secure token encoding/decoding

### 3. **Authentication Endpoints**

#### `POST /auth/signup`
Create a new user account.
```json
{
  "username": "alice",
  "password": "securepassword123"
}
```
Returns: `{"id": "...", "username": "alice"}`

#### `POST /auth/login`
Authenticate and receive tokens.
```json
{
  "username": "alice",
  "password": "securepassword123"
}
```
Returns:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `POST /auth/refresh`
Refresh access token using refresh token.
```json
{
  "refresh_token": "eyJ..."
}
```
Returns new access and refresh tokens.

#### `GET /auth/me`
Get current authenticated user info.
Requires: `Authorization: Bearer <access_token>`

### 4. **Protected Routes**

All API routes now require authentication:
- `POST /conversations` - Requires auth, auto-adds current user as member
- `GET /conversations/{id}/messages` - Requires auth + conversation membership
- `POST /messages` - Requires auth, enforces sender_id matches authenticated user

### 5. **Secure WebSocket**

WebSocket endpoint changed from `/ws/{user_id}` to `/ws` with token authentication.

**Connection Methods:**
1. Query parameter: `ws://localhost:8000/ws?token=<access_token>`
2. Authorization header: `Authorization: Bearer <access_token>`

**Security Features:**
- Token validated on connection
- User ID extracted from token (not from URL)
- Permission checks on join and message operations
- Automatic sender_id enforcement

## Usage Examples

### REST API with Authentication

```python
import requests

# 1. Sign up
response = requests.post("http://localhost:8000/auth/signup", json={
    "username": "alice",
    "password": "mypassword"
})
user = response.json()

# 2. Login
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "alice",
    "password": "mypassword"
})
tokens = response.json()
access_token = tokens["access_token"]

# 3. Use protected endpoint
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    "http://localhost:8000/conversations",
    json={"title": "Chat", "member_ids": []},
    headers=headers
)
```

### WebSocket with Authentication

```javascript
// Get token first via login
const token = "eyJ..."; // from /auth/login

// Connect with token
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
    console.log("Connected");

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

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received:", data);
};
```

## Security Best Practices Implemented

1. **Password Hashing**: Argon2 (memory-hard, resistant to GPU attacks)
2. **Token Expiry**: Short-lived access tokens, longer refresh tokens
3. **Token Type Validation**: Prevents using refresh tokens as access tokens
4. **Permission Checks**:
   - Conversation membership verified
   - Sender ID must match authenticated user
   - WebSocket operations require membership
5. **Secure Token Storage**: Tokens in HTTP-only cookies (recommended for production)
6. **Error Handling**: Generic error messages to prevent user enumeration

## Configuration

### Environment Variables

Set `SECRET_KEY` environment variable for production:
```bash
export SECRET_KEY="your-very-secure-secret-key-minimum-32-characters"
```

Default (dev only): `"your-secret-key-change-in-production-min-32-chars"`

### Token Expiry Settings

In `app/auth.py`:
- `ACCESS_TOKEN_EXPIRE_MINUTES = 30`
- `REFRESH_TOKEN_EXPIRE_DAYS = 7`

## Testing

Comprehensive test suite in `tests/test_auth.py`:

- ✅ Signup success/duplicate username
- ✅ Login success/wrong password
- ✅ Token validation
- ✅ Token refresh
- ✅ Protected route access
- ✅ WebSocket authentication
- ✅ Permission enforcement
- ✅ Token expiry
- ✅ Invalid token rejection

Run tests:
```bash
pytest tests/test_auth.py -v
```

## Migration Notes

### Breaking Changes

1. **User Creation**: Now requires password
   - Old: `POST /users {"username": "alice"}`
   - New: `POST /auth/signup {"username": "alice", "password": "pass"}`

2. **WebSocket Endpoint**: Changed from `/ws/{user_id}` to `/ws?token=...`
   - Old: `ws://localhost:8000/ws/user-id`
   - New: `ws://localhost:8000/ws?token=access_token`

3. **All Routes Protected**: Require `Authorization: Bearer <token>` header

### Database Migration

The `User` model now includes `password_hash` field. Existing databases will need migration:

```python
# Run this once to add password_hash column to existing users
# (set a default password or mark as requiring password reset)
```

## Future Enhancements

1. **Password Reset**: Email-based password reset flow
2. **Token Blacklisting**: Revoke tokens on logout
3. **Rate Limiting**: Prevent brute force attacks
4. **2FA**: Two-factor authentication
5. **OAuth**: Social login integration
6. **Session Management**: Track active sessions per user
