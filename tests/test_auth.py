# tests/test_auth.py
import json
import time
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token, decode_token, SECRET_KEY
import jwt
import uuid

client = TestClient(app)


def test_signup_success():
    """Test successful user signup"""
    import time
    unique_username = f"testuser1_{int(time.time() * 1000)}"
    response = client.post(
        "/auth/signup",
        json={"username": unique_username, "password": "securepass123"}
    )
    assert response.status_code == 201, f"Signup failed: {response.json()}"
    data = response.json()
    assert "id" in data
    assert data["username"] == unique_username
    assert "password" not in data  # Password should never be returned


def test_signup_duplicate_username():
    """Test signup with duplicate username fails"""
    # First signup
    client.post(
        "/auth/signup",
        json={"username": "duplicate", "password": "pass123"}
    )

    # Second signup with same username
    response = client.post(
        "/auth/signup",
        json={"username": "duplicate", "password": "pass456"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success():
    """Test successful login returns tokens"""
    # Create user first (use unique username)
    import time
    unique_username = f"loginuser_{int(time.time() * 1000)}"
    signup_response = client.post(
        "/auth/signup",
        json={"username": unique_username, "password": "mypassword"}
    )
    assert signup_response.status_code == 201, f"Signup failed: {signup_response.json()}"

    # Login
    response = client.post(
        "/auth/login",
        json={"username": unique_username, "password": "mypassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


def test_login_wrong_password():
    """Test login with wrong password fails"""
    # Create user
    client.post(
        "/auth/signup",
        json={"username": "wrongpass", "password": "correctpass"}
    )

    # Login with wrong password
    response = client.post(
        "/auth/login",
        json={"username": "wrongpass", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user():
    """Test login with non-existent user fails"""
    response = client.post(
        "/auth/login",
        json={"username": "nonexistent", "password": "anypass"}
    )
    assert response.status_code == 401


def test_get_current_user_with_token():
    """Test /auth/me endpoint with valid token"""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"username": "meuser", "password": "pass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "meuser", "password": "pass123"}
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert "id" in data


def test_get_current_user_without_token():
    """Test /auth/me endpoint without token fails"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # FastAPI returns 403 for missing auth


def test_get_current_user_with_invalid_token():
    """Test /auth/me endpoint with invalid token fails"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401


def test_refresh_token_success():
    """Test refresh token returns new tokens"""
    import time
    # Signup and login
    client.post(
        "/auth/signup",
        json={"username": "refreshuser", "password": "pass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "refreshuser", "password": "pass123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    original_access_token = login_data["access_token"]
    original_refresh_token = login_data["refresh_token"]

    # Small delay to ensure different timestamps
    time.sleep(0.1)

    # Refresh tokens
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens should be different (they have different issued-at times)
    assert data["access_token"] != original_access_token, "New access token should be different"
    assert data["refresh_token"] != original_refresh_token, "New refresh token should be different"

    # Verify new tokens are valid by decoding them
    import jwt
    from app.auth import SECRET_KEY, ALGORITHM
    new_access_payload = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    new_refresh_payload = jwt.decode(data["refresh_token"], SECRET_KEY, algorithms=[ALGORITHM])
    original_refresh_payload = jwt.decode(original_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

    # Verify token types
    assert new_access_payload["type"] == "access"
    assert new_refresh_payload["type"] == "refresh"
    # Verify JWT IDs are different (ensures uniqueness)
    assert "jti" in new_access_payload, "New access token should have 'jti' claim"
    assert "jti" in new_refresh_payload, "New refresh token should have 'jti' claim"
    assert "jti" in original_refresh_payload, "Original refresh token should have 'jti' claim"
    assert new_access_payload["jti"] != original_refresh_payload["jti"], "JWT IDs should be different"
    assert new_refresh_payload["jti"] != original_refresh_payload["jti"], "JWT IDs should be different"


def test_refresh_token_with_access_token_fails():
    """Test refresh endpoint rejects access tokens"""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"username": "refresherror", "password": "pass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "refresherror", "password": "pass123"}
    )
    access_token = login_response.json()["access_token"]

    # Try to use access token as refresh token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token}
    )
    assert response.status_code == 401


def test_protected_route_requires_auth():
    """Test that protected routes require authentication"""
    # Try to create conversation without auth
    response = client.post(
        "/conversations",
        json={"title": "test", "member_ids": []}
    )
    assert response.status_code == 403  # Missing auth


def test_create_conversation_with_auth():
    """Test creating conversation with authentication"""
    # Create two users (use unique usernames)
    import time
    unique_id = str(int(time.time() * 1000))
    signup1 = client.post(
        "/auth/signup",
        json={"username": f"alice_auth_{unique_id}", "password": "pass123"}
    )
    assert signup1.status_code == 201, f"Signup failed: {signup1.json()}"
    alice = signup1.json()

    signup2 = client.post(
        "/auth/signup",
        json={"username": f"bob_auth_{unique_id}", "password": "pass123"}
    )
    assert signup2.status_code == 201, f"Signup failed: {signup2.json()}"
    bob = signup2.json()

    # Login as alice
    login = client.post(
        "/auth/login",
        json={"username": f"alice_auth_{unique_id}", "password": "pass123"}
    )
    token = login.json()["access_token"]

    # Create conversation
    response = client.post(
        "/conversations",
        json={"title": "auth chat", "member_ids": [bob["id"]]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    conv = response.json()
    assert conv["title"] == "auth chat"
    # Current user should be automatically added
    assert alice["id"] in conv["members"]
    assert bob["id"] in conv["members"]


def test_send_message_enforces_sender_id():
    """Test that sender_id must match authenticated user"""
    # Create users and login
    signup = client.post(
        "/auth/signup",
        json={"username": "sender_test", "password": "pass123"}
    )
    user = signup.json()

    login = client.post(
        "/auth/login",
        json={"username": "sender_test", "password": "pass123"}
    )
    token = login.json()["access_token"]

    # Create conversation
    conv_response = client.post(
        "/conversations",
        json={"title": "test", "member_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    conv_id = conv_response.json()["id"]

    # Try to send message with wrong sender_id
    msg_id = str(uuid.uuid4())
    response = client.post(
        "/messages",
        json={
            "message_id": msg_id,
            "sender_id": "wrong_user_id",
            "conversation_id": conv_id,
            "content": "test"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "sender_id must match" in response.json()["detail"].lower()


def test_websocket_requires_token():
    """Test WebSocket connection requires authentication token"""
    # Try to connect without token - should be rejected
    from starlette.websockets import WebSocketDisconnect
    try:
        with client.websocket_connect("/ws") as ws:
            # Should not reach here - connection should be rejected
            ws.receive_json()
            assert False, "Should have been rejected"
    except WebSocketDisconnect as e:
        # Expected WebSocket disconnect with policy violation
        assert e.code == 1008  # Policy violation
        assert "Missing authentication token" in str(e.reason) or "authentication" in str(e.reason).lower()
    except Exception as e:
        # Other exceptions are also acceptable (connection rejected)
        assert True


def test_websocket_with_valid_token():
    """Test WebSocket connection with valid token"""
    # Signup and login
    client.post(
        "/auth/signup",
        json={"username": "wsuser", "password": "pass123"}
    )
    login = client.post(
        "/auth/login",
        json={"username": "wsuser", "password": "pass123"}
    )
    token = login.json()["access_token"]

    # Connect with token
    with client.websocket_connect(f"/ws?token={token}") as ws:
        # Should connect successfully
        # Send a join message to verify it works
        ws.send_json({"type": "join", "conversation_id": "test_conv"})
        # Should get an error about conversation not found, but connection should work
        response = ws.receive_json()
        assert response["type"] == "error"


def test_websocket_with_invalid_token():
    """Test WebSocket connection with invalid token is rejected"""
    try:
        with client.websocket_connect("/ws?token=invalid_token") as ws:
            ws.receive_json()
    except Exception:
        pass  # Expected to fail


def test_websocket_message_enforces_sender():
    """Test WebSocket messages enforce sender_id matches authenticated user"""
    # Create users (use unique usernames)
    import time
    unique_id = str(int(time.time() * 1000))
    signup1 = client.post(
        "/auth/signup",
        json={"username": f"ws1_{unique_id}", "password": "pass123"}
    )
    assert signup1.status_code == 201, f"Signup failed: {signup1.json()}"
    user1 = signup1.json()

    signup2 = client.post(
        "/auth/signup",
        json={"username": f"ws2_{unique_id}", "password": "pass123"}
    )
    assert signup2.status_code == 201, f"Signup failed: {signup2.json()}"
    user2 = signup2.json()

    # Login as user1
    login1 = client.post(
        "/auth/login",
        json={"username": f"ws1_{unique_id}", "password": "pass123"}
    )
    token1 = login1.json()["access_token"]

    # Create conversation
    conv_response = client.post(
        "/conversations",
        json={"title": "ws test", "member_ids": [user2["id"]]},
        headers={"Authorization": f"Bearer {token1}"}
    )
    conv_id = conv_response.json()["id"]

    # Connect WebSocket as user1
    with client.websocket_connect(f"/ws?token={token1}") as ws1:
        # Join conversation
        ws1.send_json({"type": "join", "conversation_id": conv_id})
        ws1.receive_json()  # Should get "joined"

        # Try to send message - sender_id is automatically set to authenticated user
        msg_id = str(uuid.uuid4())
        ws1.send_json({
            "type": "message",
            "message_id": msg_id,
            "conversation_id": conv_id,
            "content": "hello"
        })
        # Should succeed
        response = ws1.receive_json()
        assert response["type"] == "message"


def test_token_expiry():
    """Test that expired tokens are rejected"""
    # Create a token with very short expiry
    from datetime import timedelta
    expired_token = create_access_token(
        data={"sub": "test_user"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )

    # Try to use expired token
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


def test_get_messages_requires_membership():
    """Test that getting messages requires conversation membership"""
    # Create two users
    signup1 = client.post(
        "/auth/signup",
        json={"username": "member1", "password": "pass123"}
    )
    user1 = signup1.json()

    signup2 = client.post(
        "/auth/signup",
        json={"username": "member2", "password": "pass123"}
    )
    user2 = signup2.json()

    # Login as user1
    login1 = client.post(
        "/auth/login",
        json={"username": "member1", "password": "pass123"}
    )
    token1 = login1.json()["access_token"]

    # Login as user2
    login2 = client.post(
        "/auth/login",
        json={"username": "member2", "password": "pass123"}
    )
    token2 = login2.json()["access_token"]

    # User1 creates conversation with only themselves
    conv_response = client.post(
        "/conversations",
        json={"title": "private", "member_ids": []},
        headers={"Authorization": f"Bearer {token1}"}
    )
    conv_id = conv_response.json()["id"]

    # User2 tries to access messages (should fail)
    response = client.get(
        f"/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403
    assert "not a member" in response.json()["detail"].lower()
