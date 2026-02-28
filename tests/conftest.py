import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Reusable auth helpers ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePass1!", "full_name": "Test User"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecurePass1!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def checking_account(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/api/v1/accounts/",
        json={"account_type": "CHECKING", "currency": "USD"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()
