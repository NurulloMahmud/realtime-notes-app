import pytest


@pytest.mark.asyncio
async def test_add_collaborator_by_email(client, auth_headers):
    await client.post("/auth/register", json={"email": "collab@example.com", "username": "collabuser", "password": "password123"})
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"email": "collab@example.com"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "collab@example.com"
    assert data["note_id"] == note_id


@pytest.mark.asyncio
async def test_add_collaborator_by_user_id(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["user_id"] == second_me["id"]


@pytest.mark.asyncio
async def test_add_duplicate_collaborator(client, auth_headers):
    await client.post("/auth/register", json={"email": "dup@example.com", "username": "dupuser", "password": "password123"})
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"email": "dup@example.com"}, headers=auth_headers)
    resp = await client.post(f"/notes/{note_id}/collaborators", json={"email": "dup@example.com"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "already" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_add_nonexistent_user(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"email": "ghost@example.com"}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_collaborator_to_nonexistent_note(client, auth_headers):
    resp = await client.post("/notes/00000000-0000-0000-0000-000000000001/collaborators", json={"email": "x@x.com"}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_collaborator_neither_email_nor_user_id(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_add_owner_as_collaborator(client, auth_headers):
    owner_data = (await client.get("/auth/me", headers=auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"user_id": owner_data["id"]}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Owner" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_non_owner_cannot_add_collaborator(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"email": "anyone@example.com"}, headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_add_collaborator_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/collaborators", json={"email": "x@x.com"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_collaborators_success(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/collaborators", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["username"] == "seconduser"


@pytest.mark.asyncio
async def test_list_collaborators_empty(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/collaborators", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_collaborators_by_collaborator(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/collaborators", headers=second_auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_collaborators_nonexistent_note(client, auth_headers):
    resp = await client.get("/notes/00000000-0000-0000-0000-000000000001/collaborators", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_collaborators_by_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Private", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/collaborators", headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_collaborators_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/collaborators")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_remove_collaborator_success(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.delete(f"/notes/{note_id}/collaborators/{second_me['id']}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_remove_nonexistent_collaborator(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.delete(f"/notes/{note_id}/collaborators/00000000-0000-0000-0000-000000000001", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_remove_collaborator_from_nonexistent_note(client, auth_headers):
    resp = await client.delete("/notes/00000000-0000-0000-0000-000000000001/collaborators/00000000-0000-0000-0000-000000000002", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_non_owner_cannot_remove_collaborator(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.delete(f"/notes/{note_id}/collaborators/{second_me['id']}", headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_remove_collaborator_unauthenticated(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.delete(f"/notes/{note_id}/collaborators/{second_me['id']}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_removed_collaborator_loses_access(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)
    assert (await client.get(f"/notes/{note_id}", headers=second_auth_headers)).status_code == 200

    await client.delete(f"/notes/{note_id}/collaborators/{second_me['id']}", headers=auth_headers)
    assert (await client.get(f"/notes/{note_id}", headers=second_auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_collaborator_appears_in_list_after_add(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    list_resp = await client.get(f"/notes/{note_id}/collaborators", headers=auth_headers)
    assert any(c["user_id"] == second_me["id"] for c in list_resp.json())


@pytest.mark.asyncio
async def test_collaborator_absent_after_remove(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)
    await client.delete(f"/notes/{note_id}/collaborators/{second_me['id']}", headers=auth_headers)

    list_resp = await client.get(f"/notes/{note_id}/collaborators", headers=auth_headers)
    assert not any(c["user_id"] == second_me["id"] for c in list_resp.json())
