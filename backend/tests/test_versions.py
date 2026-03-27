import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_version_created_on_note_create(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 1
    assert versions[0]["content"] == "v0"


@pytest.mark.asyncio
async def test_versions_grow_with_updates(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.patch(f"/notes/{note_id}", json={"content": "v1"}, headers=auth_headers)
    await client.patch(f"/notes/{note_id}", json={"content": "v2"}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_version_no_new_entry_on_title_only_update(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.patch(f"/notes/{note_id}", json={"title": "New Title"}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_version_history_limit_enforced(client, auth_headers):
    with patch("app.services.versions.settings") as mock_settings:
        mock_settings.VERSION_HISTORY_LIMIT = 3
        create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
        note_id = create_resp.json()["id"]

        for i in range(1, 5):
            await client.patch(f"/notes/{note_id}", json={"content": f"v{i}"}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


@pytest.mark.asyncio
async def test_versions_ordered_newest_first(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "first"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    await client.patch(f"/notes/{note_id}", json={"content": "second"}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    versions = resp.json()
    assert versions[0]["content"] == "second"
    assert versions[1]["content"] == "first"


@pytest.mark.asyncio
async def test_version_includes_editor_username(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    assert resp.json()[0]["editor_username"] == "testuser"


@pytest.mark.asyncio
async def test_list_versions_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.get(f"/notes/{note_id}/versions")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_versions_nonexistent_note(client, auth_headers):
    resp = await client.get("/notes/00000000-0000-0000-0000-000000000001/versions", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_versions_by_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Private", "content": ""}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    resp = await client.get(f"/notes/{note_id}/versions", headers=second_auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_versions_by_collaborator(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Shared", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)

    resp = await client.get(f"/notes/{note_id}/versions", headers=second_auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_restore_version_success(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    await client.patch(f"/notes/{note_id}", json={"content": "modified"}, headers=auth_headers)

    versions_resp = await client.get(f"/notes/{note_id}/versions", headers=auth_headers)
    versions = versions_resp.json()
    old_version = next(v for v in versions if v["content"] == "original")

    resp = await client.post(f"/notes/{note_id}/versions/{old_version['id']}/restore", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "original"


@pytest.mark.asyncio
async def test_restore_version_updates_note_content(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "original"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    await client.patch(f"/notes/{note_id}", json={"content": "modified"}, headers=auth_headers)

    versions = (await client.get(f"/notes/{note_id}/versions", headers=auth_headers)).json()
    old_version = next(v for v in versions if v["content"] == "original")

    await client.post(f"/notes/{note_id}/versions/{old_version['id']}/restore", headers=auth_headers)

    note_resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert note_resp.json()["content"] == "original"


@pytest.mark.asyncio
async def test_restore_version_by_collaborator(client, auth_headers, second_auth_headers):
    second_me = (await client.get("/auth/me", headers=second_auth_headers)).json()
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    await client.post(f"/notes/{note_id}/collaborators", json={"user_id": second_me["id"]}, headers=auth_headers)
    await client.patch(f"/notes/{note_id}", json={"content": "v1"}, headers=auth_headers)

    versions = (await client.get(f"/notes/{note_id}/versions", headers=auth_headers)).json()
    old_version = next(v for v in versions if v["content"] == "v0")

    resp = await client.post(f"/notes/{note_id}/versions/{old_version['id']}/restore", headers=second_auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_restore_nonexistent_version(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]

    resp = await client.post(f"/notes/{note_id}/versions/00000000-0000-0000-0000-000000000001/restore", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_restore_version_wrong_note(client, auth_headers):
    note1 = (await client.post("/notes", json={"title": "Note1", "content": "v0"}, headers=auth_headers)).json()
    note2 = (await client.post("/notes", json={"title": "Note2", "content": "x"}, headers=auth_headers)).json()

    versions = (await client.get(f"/notes/{note1['id']}/versions", headers=auth_headers)).json()
    version_id = versions[0]["id"]

    resp = await client.post(f"/notes/{note2['id']}/versions/{version_id}/restore", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_restore_version_unauthenticated(client, auth_headers):
    create_resp = await client.post("/notes", json={"title": "Note", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    versions = (await client.get(f"/notes/{note_id}/versions", headers=auth_headers)).json()

    resp = await client.post(f"/notes/{note_id}/versions/{versions[0]['id']}/restore")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_restore_version_by_stranger(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/notes", json={"title": "Private", "content": "v0"}, headers=auth_headers)
    note_id = create_resp.json()["id"]
    versions = (await client.get(f"/notes/{note_id}/versions", headers=auth_headers)).json()

    resp = await client.post(f"/notes/{note_id}/versions/{versions[0]['id']}/restore", headers=second_auth_headers)
    assert resp.status_code == 403
