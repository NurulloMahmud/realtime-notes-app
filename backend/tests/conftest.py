import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def registered_user(client):
    await client.post("/auth/register", json={"email": "test@example.com", "username": "testuser", "password": "password123"})
    resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    tokens = resp.json()
    return {"access_token": tokens["access_token"], "email": "test@example.com", "username": "testuser"}


@pytest_asyncio.fixture
async def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest_asyncio.fixture
async def second_user(client):
    await client.post("/auth/register", json={"email": "second@example.com", "username": "seconduser", "password": "password123"})
    resp = await client.post("/auth/login", json={"email": "second@example.com", "password": "password123"})
    tokens = resp.json()
    return {"access_token": tokens["access_token"], "email": "second@example.com", "username": "seconduser"}


@pytest_asyncio.fixture
async def second_auth_headers(second_user):
    return {"Authorization": f"Bearer {second_user['access_token']}"}
