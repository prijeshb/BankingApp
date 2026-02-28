"""Health endpoint tests."""
import pytest
from httpx import AsyncClient


async def test_health_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert "version" in data
    assert "timestamp" in data


async def test_health_ready(client: AsyncClient):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


async def test_health_live(client: AsyncClient):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


async def test_health_no_auth_required(client: AsyncClient):
    """Health endpoints must be publicly accessible — no token needed."""
    for path in ["/health", "/health/ready", "/health/live"]:
        resp = await client.get(path)
        assert resp.status_code != 401
