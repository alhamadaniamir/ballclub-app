import pytest

pytestmark = pytest.mark.asyncio


async def test_login_rejects_wrong_password(client):
    res = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


async def test_login_succeeds_with_correct_credentials(client):
    res = await client.post("/api/auth/login", json={"username": "admin", "password": "test-password-123"})
    assert res.status_code == 200
    assert "token" in res.json()


async def test_protected_route_requires_token(client):
    res = await client.get("/api/sessions/")
    assert res.status_code == 401


async def test_login_is_rate_limited(client):
    codes = [
        (await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})).status_code
        for _ in range(7)
    ]
    assert 429 in codes


async def test_get_me(client, auth_headers):
    res = await client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "admin"
    assert data["first_name"] == ""
    assert data["last_name"] == ""


async def test_update_profile(client, auth_headers):
    res = await client.patch(
        "/api/auth/me/profile",
        headers=auth_headers,
        json={"username": "admin", "first_name": "Ada", "last_name": "Owner"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["first_name"] == "Ada"
    assert data["last_name"] == "Owner"

    res = await client.get("/api/auth/me", headers=auth_headers)
    assert res.json()["first_name"] == "Ada"


async def test_update_profile_rejects_short_username(client, auth_headers):
    res = await client.patch(
        "/api/auth/me/profile", headers=auth_headers, json={"username": "ab"}
    )
    assert res.status_code == 400


async def test_update_profile_rejects_duplicate_username(client, auth_headers):
    await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "hunter2222"})
    res = await client.patch(
        "/api/auth/me/profile", headers=auth_headers, json={"username": "second-owner"}
    )
    assert res.status_code == 400


async def test_get_me_requires_auth(client):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401


async def test_change_own_password(client, auth_headers):
    res = await client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"current_password": "test-password-123", "new_password": "new-password-456"},
    )
    assert res.status_code == 200

    res = await client.post("/api/auth/login", json={"username": "admin", "password": "new-password-456"})
    assert res.status_code == 200


async def test_change_password_rejects_wrong_current_password(client, auth_headers):
    res = await client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"current_password": "wrong", "new_password": "new-password-456"},
    )
    assert res.status_code == 401


async def test_change_password_rejects_short_new_password(client, auth_headers):
    res = await client.patch(
        "/api/auth/me",
        headers=auth_headers,
        json={"current_password": "test-password-123", "new_password": "short"},
    )
    assert res.status_code == 400
