import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app
from app.database import get_db
from tests.conftest import override_get_db, TestSessionLocal

app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_websocket_invalid_token(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "WS Note", "content": "initial"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/ws/notes/{note_id}?token=invalid.token.here"):
                pass


@pytest.mark.asyncio
async def test_websocket_missing_token(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "WS Note", "content": "initial"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(Exception):
            with tc.websocket_connect(f"/ws/notes/{note_id}"):
                pass


@pytest.mark.asyncio
async def test_websocket_nonexistent_note(client, auth_headers, registered_user):
    token = registered_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/ws/notes/00000000-0000-0000-0000-000000000001?token={token}"):
                pass


@pytest.mark.asyncio
async def test_websocket_no_access(client, auth_headers, second_user):
    create_resp = await client.post("/notes", json={"title": "Private", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token2 = second_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(WebSocketDisconnect):
            with tc.websocket_connect(f"/ws/notes/{note_id}?token={token2}"):
                pass


@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect(client, auth_headers, registered_user):
    create_resp = await client.post("/notes", json={"title": "WS Note", "content": "initial"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token = registered_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token}") as ws:
            ws.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_websocket_invalid_json_ignored(client, auth_headers, registered_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token = registered_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token}") as ws:
            ws.send_text("this is not json {{{{")
            ws.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_websocket_unknown_message_type_ignored(client, auth_headers, registered_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token = registered_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token}") as ws:
            ws.send_json({"type": "unknown_type", "data": "anything"})
            ws.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_websocket_edit_content_too_long_ignored(client, auth_headers, registered_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token = registered_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token}") as ws:
            ws.send_json({"type": "edit", "content": "x" * 50001, "cursor_position": 0})

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.json()["content"] == "original"


@pytest.mark.asyncio
async def test_websocket_edit_saves_to_db(client, auth_headers, second_auth_headers, registered_user, second_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    token1 = registered_user["access_token"]
    token2 = second_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token1}") as ws1:
            with tc.websocket_connect(f"/ws/notes/{note_id}?token={token2}") as ws2:
                ws1.receive_json()
                ws1.send_json({"type": "edit", "content": "saved via ws", "cursor_position": 0})
                msg = ws2.receive_json()
                assert msg["type"] == "update"

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.json()["content"] == "saved via ws"


@pytest.mark.asyncio
async def test_websocket_broadcast_to_other_client(client, auth_headers, second_auth_headers, registered_user, second_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    token1 = registered_user["access_token"]
    token2 = second_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token1}") as ws1:
            with tc.websocket_connect(f"/ws/notes/{note_id}?token={token2}") as ws2:
                ws1.receive_json()
                ws1.send_json({"type": "edit", "content": "broadcast test", "cursor_position": 5})
                msg = ws2.receive_json()
                assert msg["type"] == "update"
                assert msg["content"] == "broadcast test"
                assert msg["username"] == "testuser"
                assert "timestamp" in msg


@pytest.mark.asyncio
async def test_websocket_presence_join_broadcast(client, auth_headers, second_auth_headers, registered_user, second_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    token1 = registered_user["access_token"]
    token2 = second_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token1}") as ws1:
            with tc.websocket_connect(f"/ws/notes/{note_id}?token={token2}"):
                msg = ws1.receive_json()
                assert msg["type"] == "presence"
                assert msg["status"] == "joined"
                assert msg["username"] == "seconduser"


@pytest.mark.asyncio
async def test_websocket_edit_not_sent_back_to_sender(client, auth_headers, registered_user):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    token = registered_user["access_token"]

    import threading

    received = []

    def ws_session():
        with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
            tc = TestClient(app, raise_server_exceptions=False)
            with tc.websocket_connect(f"/ws/notes/{note_id}?token={token}") as ws:
                ws.send_json({"type": "edit", "content": "no echo", "cursor_position": 0})
                ws.close()

    t = threading.Thread(target=ws_session)
    t.start()
    t.join(timeout=5)

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_websocket_collaborator_can_connect(client, auth_headers, second_auth_headers, second_user):
    create_resp = await client.post("/notes", json={"title": "Shared", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    token2 = second_user["access_token"]

    with patch("app.routers.websocket.AsyncSessionLocal", TestSessionLocal):
        tc = TestClient(app, raise_server_exceptions=False)
        with tc.websocket_connect(f"/ws/notes/{note_id}?token={token2}") as ws:
            ws.send_json({"type": "ping"})
