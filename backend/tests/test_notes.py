import pytest


@pytest.mark.asyncio
async def test_create_note_success(client, auth_headers):
    resp = await client.post("/notes", json={"title": "My Note", "content": "Hello"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Note"
    assert data["content"] == "Hello"
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_note_default_empty_content(client, auth_headers):
    resp = await client.post("/notes", json={"title": "No Content"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["content"] == ""


@pytest.mark.asyncio
async def test_create_note_unauthenticated(client):
    resp = await client.post("/notes", json={"title": "Note", "content": ""})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_note_empty_title(client, auth_headers):
    resp = await client.post("/notes", json={"title": "", "content": ""}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_title_max_boundary(client, auth_headers):
    resp = await client.post("/notes", json={"title": "a" * 255, "content": ""}, headers=auth_headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_note_title_too_long(client, auth_headers):
    resp = await client.post("/notes", json={"title": "a" * 256, "content": ""}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_missing_title(client, auth_headers):
    resp = await client.post("/notes", json={"content": "some content"}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_content_max_boundary(client, auth_headers):
    resp = await client.post("/notes", json={"title": "Note", "content": "a" * 50000}, headers=auth_headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_note_content_too_long(client, auth_headers):
    resp = await client.post("/notes", json={"title": "Note", "content": "a" * 50001}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_notes_success(client, auth_headers):
    await client.post("/notes", json={"title": "Note 1", "content": ""}, headers=auth_headers)
    await client.post("/notes", json={"title": "Note 2", "content": ""}, headers=auth_headers)
    resp = await client.get("/notes", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_notes_empty(client, auth_headers):
    resp = await client.get("/notes", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_notes_unauthenticated(client):
    resp = await client.get("/notes")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_notes_includes_collaborated(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Shared", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get("/notes", headers=second_auth_headers)
    assert resp.status_code == 200
    assert any(n["id"] == note_id for n in resp.json())


@pytest.mark.asyncio
async def test_list_notes_does_not_show_others_notes(client, auth_headers, second_auth_headers):
    await client.post("/notes", json={"title": "Private", "content": ""}, headers=auth_headers)

    resp = await client.get("/notes", headers=second_auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_note_success(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Detail", "content": "Content"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Content"
    assert "collaborators" in data


@pytest.mark.asyncio
async def test_get_note_shows_collaborators_list(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 200
    collabs = resp.json()["collaborators"]
    assert len(collabs) == 1
    assert collabs[0]["username"] == "seconduser"


@pytest.mark.asyncio
async def test_get_note_nonexistent(client, auth_headers):
    resp = await client.get("/notes/00000000-0000-0000-0000-000000000001", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_note_as_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Private", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}", headers=second_auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_note_as_collaborator(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Shared", "content": "data"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}", headers=second_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "data"


@pytest.mark.asyncio
async def test_get_note_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.get(f"/notes/{note_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_note_title_only(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Old Title", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"title": "New Title"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["content"] == "original"


@pytest.mark.asyncio
async def test_update_note_content_only(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Title", "content": "old"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"content": "new content"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Title"
    assert data["content"] == "new content"


@pytest.mark.asyncio
async def test_update_note_both_fields(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Old", "content": "old"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"title": "New", "content": "new"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New"
    assert data["content"] == "new"


@pytest.mark.asyncio
async def test_update_note_nonexistent(client, auth_headers):
    resp = await client.patch("/notes/00000000-0000-0000-0000-000000000001", json={"title": "X"}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_note_by_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Private", "content": "data"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"title": "Hacked"}, headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_note_by_collaborator(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Shared", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.patch(f"/notes/{note_id}", json={"content": "collab edit"}, headers=second_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "collab edit"


@pytest.mark.asyncio
async def test_update_note_content_too_long(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"content": "a" * 50001}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_note_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.patch(f"/notes/{note_id}", json={"title": "X"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_note_owner(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Delete me", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.delete(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_note_nonexistent(client, auth_headers):
    resp = await client.delete("/notes/00000000-0000-0000-0000-000000000001", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_by_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Protected", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.delete(f"/notes/{note_id}", headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_note_by_collaborator(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Protected", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.delete(f"/notes/{note_id}", headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_note_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.delete(f"/notes/{note_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_note_not_accessible_after_deletion(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Gone", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    await client.delete(f"/notes/{note_id}", headers=auth_headers)
    resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_note_not_listed_after_deletion(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Gone", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    await client.delete(f"/notes/{note_id}", headers=auth_headers)
    resp = await client.get("/notes", headers=auth_headers)
    assert resp.status_code == 200
    assert not any(n["id"] == note_id for n in resp.json())
