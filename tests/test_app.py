# tests/test_app.py
import json
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def test_create_user_and_conv_and_send_http_message():
    # create two users
    r = client.post("/users", json={"username": "alice"})
    assert r.status_code == 201
    alice = r.json()
    r = client.post("/users", json={"username": "bob"})
    assert r.status_code == 201
    bob = r.json()

    # create conversation
    r = client.post("/conversations", json={"title": "chat", "member_ids": [alice["id"], bob["id"]]})
    assert r.status_code == 201
    conv = r.json()

    # send a message via HTTP
    msg_id = str(uuid.uuid4())
    payload = {
        "message_id": msg_id,
        "sender_id": alice["id"],
        "conversation_id": conv["id"],
        "content": "hello bob"
    }
    r = client.post("/messages", json=payload)
    assert r.status_code == 201
    saved = r.json()
    assert saved["content"] == "hello bob"

    # fetching messages
    r = client.get(f"/conversations/{conv['id']}/messages")
    assert r.status_code == 200
    messages = r.json()["messages"]
    assert any(m["message_id"] == msg_id for m in messages)


def test_websocket_send_and_receive():
    # create users & conv
    r = client.post("/users", json={"username": "w1"})
    u1 = r.json()
    r = client.post("/users", json={"username": "w2"})
    u2 = r.json()
    r = client.post("/conversations", json={"title": "ws", "member_ids": [u1["id"], u2["id"]]})
    conv = r.json()

    # connect websockets for both users
    with client.websocket_connect(f"/ws/{u1['id']}") as ws1, client.websocket_connect(f"/ws/{u2['id']}") as ws2:
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
