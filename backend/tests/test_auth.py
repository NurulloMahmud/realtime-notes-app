import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={"email": "user@example.com", "username": "newuser", "password": "securepass"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "created_at" in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={"email": "dup@example.com", "username": "user1", "password": "password1"})
    resp = await client.post("/auth/register", json={"email": "dup@example.com", "username": "user2", "password": "password2"})
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post("/auth/register", json={"email": "first@example.com", "username": "sameuser", "password": "password1"})
    resp = await client.post("/auth/register", json={"email": "second@example.com", "username": "sameuser", "password": "password2"})
    assert resp.status_code == 400
    assert "Username" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email_format(client):
    resp = await client.post("/auth/register", json={"email": "not-an-email", "username": "validuser", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_username_too_short(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "ab", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_username_too_long(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "a" * 33, "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_username_with_spaces(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "bad user", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_username_with_special_chars(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "bad@user!", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_username_min_boundary(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "abc", "password": "password123"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_username_max_boundary(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "a" * 32, "password": "password123"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_password_too_short(client):
    resp = await client.post("/auth/register", json={"email": "bad@example.com", "username": "validuser", "password": "short"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_password_min_boundary(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "minpass", "password": "12345678"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_missing_email(client):
    resp = await client.post("/auth/register", json={"username": "user1", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_username(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client):
    resp = await client.post("/auth/register", json={"email": "a@example.com", "username": "user1"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json={"email": "login@example.com", "username": "loginuser", "password": "password123"})
    resp = await client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"email": "login2@example.com", "username": "loginuser2", "password": "password123"})
    resp = await client.post("/auth/login", json={"email": "login2@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_email(client):
    resp = await client.post("/auth/login", json={"password": "password123"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_password(client):
    resp = await client.post("/auth/login", json={"email": "a@example.com"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_token_refresh_success(client):
    await client.post("/auth/register", json={"email": "refresh@example.com", "username": "refreshuser", "password": "password123"})
    login_resp = await client.post("/auth/login", json={"email": "refresh@example.com", "password": "password123"})
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_token_refresh_invalid_token(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "totally.invalid.token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh_with_access_token(client):
    await client.post("/auth/register", json={"email": "rt@example.com", "username": "rtuser", "password": "password123"})
    login_resp = await client.post("/auth/login", json={"email": "rt@example.com", "password": "password123"})
    access_token = login_resp.json()["access_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh_missing_field(client):
    resp = await client.post("/auth/refresh", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_me_authenticated(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_malformed_header(client):
    resp = await client.get("/auth/me", headers={"Authorization": "InvalidFormat"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_me_with_refresh_token_rejected(client):
    await client.post("/auth/register", json={"email": "rtt@example.com", "username": "rttuser", "password": "password123"})
    login_resp = await client.post("/auth/login", json={"email": "rtt@example.com", "password": "password123"})
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.status_code == 401
