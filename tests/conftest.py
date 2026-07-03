import bcrypt
import httpx
import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

import app.db as db_module

OWNER_PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _mock_mongo(monkeypatch):
    monkeypatch.setattr(db_module, "AsyncIOMotorClient", lambda uri: AsyncMongoMockClient())


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.core.rate_limit import limiter

    limiter.reset()
    yield


@pytest.fixture(autouse=True)
def _owner_credentials(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "OWNER_USERNAME", "admin")
    monkeypatch.setattr(
        settings,
        "OWNER_PASSWORD_HASH",
        bcrypt.hashpw(OWNER_PASSWORD.encode(), bcrypt.gensalt()).decode(),
    )


@pytest_asyncio.fixture
async def client(_mock_mongo, _owner_credentials):
    await db_module.init_db()

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    res = await client.post("/api/auth/login", json={"username": "admin", "password": OWNER_PASSWORD})
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}
