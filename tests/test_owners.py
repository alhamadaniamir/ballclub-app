import pytest

pytestmark = pytest.mark.asyncio


async def test_bootstrapped_owner_can_log_in(client):
    res = await client.post("/api/auth/login", json={"username": "admin", "password": "test-password-123"})
    assert res.status_code == 200


async def test_create_and_login_as_new_owner(client, auth_headers):
    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "hunter2222"})
    assert res.status_code == 201
    assert res.json()["username"] == "second-owner"

    res = await client.post("/api/auth/login", json={"username": "second-owner", "password": "hunter2222"})
    assert res.status_code == 200


async def test_owner_out_includes_name_and_role(client, auth_headers):
    res = await client.post(
        "/api/owners/",
        headers=auth_headers,
        json={"username": "coach-j", "password": "hunter2222", "first_name": "Jordan", "last_name": "Blake"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["full_name"] == "Jordan Blake"
    assert data["first_name"] == "Jordan"
    assert data["last_name"] == "Blake"
    assert data["role"] == "Owner"

    # An owner without a name falls back to the username for display.
    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "nameless", "password": "hunter2222"})
    assert res.json()["full_name"] == "nameless"


async def test_duplicate_owner_username_rejected(client, auth_headers):
    await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "hunter2222"})
    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "differentpw"})
    assert res.status_code == 400


async def test_short_username_or_password_rejected(client, auth_headers):
    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "ab", "password": "hunter2222"})
    assert res.status_code == 400

    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "valid-name", "password": "short"})
    assert res.status_code == 400


async def test_search_owners_by_username(client, auth_headers):
    await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "hunter2222"})

    res = await client.get("/api/owners/", headers=auth_headers, params={"search": "second"})
    usernames = [o["username"] for o in res.json()]
    assert usernames == ["second-owner"]

    res = await client.get("/api/owners/", headers=auth_headers, params={"search": "nomatch"})
    assert res.json() == []


async def test_cannot_delete_last_owner(client, auth_headers):
    owners = (await client.get("/api/owners/", headers=auth_headers)).json()
    assert len(owners) == 1

    res = await client.delete(f"/api/owners/{owners[0]['id']}", headers=auth_headers)
    assert res.status_code == 400


async def test_can_delete_owner_when_more_than_one_remains(client, auth_headers):
    res = await client.post("/api/owners/", headers=auth_headers, json={"username": "second-owner", "password": "hunter2222"})
    new_owner_id = res.json()["id"]

    res = await client.delete(f"/api/owners/{new_owner_id}", headers=auth_headers)
    assert res.status_code == 200

    owners = (await client.get("/api/owners/", headers=auth_headers)).json()
    assert len(owners) == 1
