import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# ── File-based SQLite for tests ───────────────────────────────────────────────
# In-memory SQLite with StaticPool does not reliably share the same DB across
# different async connection acquisitions (aiosqlite spawns a thread per
# connection). A local file avoids this entirely.
_TEST_DB_PATH = "./test_banking.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    # Remove stale DB file from a previous run, if any
    if os.path.exists(_TEST_DB_PATH):
        os.remove(_TEST_DB_PATH)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()
    if os.path.exists(_TEST_DB_PATH):
        os.remove(_TEST_DB_PATH)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Wipe all rows before every test so each test starts with a clean slate."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    AsyncClient with get_db overridden to use the test engine.
    Each request gets its own session (committed on success, rolled back on error),
    matching production behaviour exactly.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Reusable helpers ──────────────────────────────────────────────────────────

VALID_USER = {
    "email": "alice@example.com",
    "password": "SecurePass1!",
    "full_name": "Alice Example",
}

SECOND_USER = {
    "email": "bob@example.com",
    "password": "SecurePass2!",
    "full_name": "Bob Example",
}


async def register_and_login(client: AsyncClient, user: dict = VALID_USER) -> dict:
    """Register a user and return {access_token, refresh_token, user_id}."""
    reg = await client.post("/api/v1/auth/register", json=user)
    assert reg.status_code == 201, reg.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert login.status_code == 200, login.text
    return {**login.json(), "user_id": reg.json()["user_id"]}


async def auth_headers(client: AsyncClient, user: dict = VALID_USER) -> dict:
    tokens = await register_and_login(client, user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def create_account(
    client: AsyncClient, headers: dict, account_type: str = "CHECKING"
) -> dict:
    resp = await client.post(
        "/api/v1/accounts/",
        json={"account_type": account_type, "currency": "USD"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
