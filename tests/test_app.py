# tests/test_app.py
import json
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def test_root_serves_index():
    """Test that root route serves index.html"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Pneumatic Chat" in response.text or "Login" in response.text


def test_static_files_served():
    """Test that static files are accessible"""
    # Test index.html
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test chat.html
    response = client.get("/static/chat.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_create_user_and_conv_and_send_http_message():
    # create two users with authentication (use unique usernames)
    import time
    unique_id = str(int(time.time() * 1000))
    r = client.post("/auth/signup", json={"username": f"alice_{unique_id}", "password": "pass123"})
    assert r.status_code == 201, f"Signup failed: {r.json()}"
    alice = r.json()

    r = client.post("/auth/signup", json={"username": f"bob_{unique_id}", "password": "pass123"})
    assert r.status_code == 201, f"Signup failed: {r.json()}"
    bob = r.json()

    # login as alice to get token
    login = client.post("/auth/login", json={"username": f"alice_{unique_id}", "password": "pass123"})
    assert login.status_code == 200
    alice_token = login.json()["access_token"]

    # create conversation (requires auth)
    r = client.post(
        "/conversations",
        json={"title": "chat", "member_ids": [bob["id"]]},
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert r.status_code == 201
    conv = r.json()

    # send a message via HTTP (requires auth)
    msg_id = str(uuid.uuid4())
    payload = {
        "message_id": msg_id,
        "sender_id": alice["id"],
        "conversation_id": conv["id"],
        "content": "hello bob"
    }
    r = client.post("/messages", json=payload, headers={"Authorization": f"Bearer {alice_token}"})
    assert r.status_code == 201
    saved = r.json()
    assert saved["content"] == "hello bob"

    # fetching messages (requires auth)
    r = client.get(f"/conversations/{conv['id']}/messages", headers={"Authorization": f"Bearer {alice_token}"})
    assert r.status_code == 200
    messages = r.json()["messages"]
    assert any(m["message_id"] == msg_id for m in messages)


def test_websocket_send_and_receive():
    # create users with authentication (use unique usernames)
    import time
    unique_id = str(int(time.time() * 1000))
    r = client.post("/auth/signup", json={"username": f"w1_{unique_id}", "password": "pass123"})
    assert r.status_code == 201, f"Signup failed: {r.json()}"
    u1 = r.json()
    r = client.post("/auth/signup", json={"username": f"w2_{unique_id}", "password": "pass123"})
    assert r.status_code == 201, f"Signup failed: {r.json()}"
    u2 = r.json()

    # login to get tokens
    login1 = client.post("/auth/login", json={"username": f"w1_{unique_id}", "password": "pass123"})
    token1 = login1.json()["access_token"]

    login2 = client.post("/auth/login", json={"username": f"w2_{unique_id}", "password": "pass123"})
    token2 = login2.json()["access_token"]

    # create conversation (requires auth)
    r = client.post(
        "/conversations",
        json={"title": "ws", "member_ids": [u2["id"]]},
        headers={"Authorization": f"Bearer {token1}"}
    )
    conv = r.json()

    # connect websockets with tokens
    with client.websocket_connect(f"/ws?token={token1}") as ws1, client.websocket_connect(f"/ws?token={token2}") as ws2:
        # join
        ws1.send_json({"type": "join", "conversation_id": conv["id"]})
        data = ws1.receive_json()
        assert data["type"] == "joined"

        ws2.send_json({"type": "join", "conversation_id": conv["id"]})
        data = ws2.receive_json()
        assert data["type"] == "joined"

        # user1 sends a message
        msg_id = str(uuid.uuid4())
        ws1.send_json({"type": "message", "message_id": msg_id, "conversation_id": conv["id"], "content": "hi"})
        # both should receive the message
        data1 = ws1.receive_json()
        data2 = ws2.receive_json()
        assert data1["type"] == "message"
        assert data2["type"] == "message"
        assert data1["message"]["message_id"] == msg_id
        assert data2["message"]["message_id"] == msg_id
