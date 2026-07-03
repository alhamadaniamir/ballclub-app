import pytest

pytestmark = pytest.mark.asyncio


async def test_create_and_list_member(client, auth_headers):
    res = await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )
    assert res.status_code == 201
    member = res.json()
    assert member["first_name"] == "Jane"
    assert member["last_name"] == "Doe"
    assert member["full_name"] == "Jane Doe"

    res = await client.get("/api/members/", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert len(body["items"]) == 1


async def test_create_member_with_middle_name(client, auth_headers):
    res = await client.post(
        "/api/members/",
        headers=auth_headers,
        json={"first_name": "Jane", "middle_name": "Q", "last_name": "Doe", "phone": "5551234567"},
    )
    assert res.status_code == 400  # middle name "Q" is only 1 character


async def test_create_member_rejects_short_name(client, auth_headers):
    res = await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "J", "last_name": "Doe", "phone": "5551234567"}
    )
    assert res.status_code == 400


async def test_create_member_rejects_invalid_phone(client, auth_headers):
    res = await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "123"}
    )
    assert res.status_code == 400


async def test_duplicate_phone_rejected(client, auth_headers):
    await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )
    res = await client.post(
        "/api/members/",
        headers=auth_headers,
        json={"first_name": "Someone", "last_name": "Else", "phone": "5551234567"},
    )
    assert res.status_code == 400


async def test_update_member(client, auth_headers):
    res = await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )
    member_id = res.json()["_id"]

    res = await client.patch(f"/api/members/{member_id}", headers=auth_headers, json={"phone": "5559998888"})
    assert res.status_code == 200
    assert res.json()["phone"] == "5559998888"


async def test_search_members_by_name_or_phone(client, auth_headers):
    await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )
    await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "John", "last_name": "Smith", "phone": "5559876543"}
    )

    res = await client.get("/api/members/", headers=auth_headers, params={"search": "jane"})
    names = [m["full_name"] for m in res.json()["items"]]
    assert names == ["Jane Doe"]

    res = await client.get("/api/members/", headers=auth_headers, params={"search": "smith"})
    names = [m["full_name"] for m in res.json()["items"]]
    assert names == ["John Smith"]

    res = await client.get("/api/members/", headers=auth_headers, params={"search": "5559876543"})
    names = [m["full_name"] for m in res.json()["items"]]
    assert names == ["John Smith"]

    res = await client.get("/api/members/", headers=auth_headers, params={"search": "nomatch"})
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_delete_member(client, auth_headers):
    res = await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )
    member_id = res.json()["_id"]

    res = await client.delete(f"/api/members/{member_id}", headers=auth_headers)
    assert res.status_code == 200

    res = await client.get("/api/members/", headers=auth_headers)
    assert res.json()["items"] == []


async def test_list_members_pagination(client, auth_headers):
    for i in range(25):
        await client.post(
            "/api/members/",
            headers=auth_headers,
            json={"first_name": f"Member{i:02d}", "last_name": "Test", "phone": f"55500000{i:02d}"},
        )

    res = await client.get("/api/members/", headers=auth_headers, params={"page": 1, "page_size": 20})
    body = res.json()
    assert body["total"] == 25
    assert len(body["items"]) == 20

    res = await client.get("/api/members/", headers=auth_headers, params={"page": 2, "page_size": 20})
    body = res.json()
    assert body["total"] == 25
    assert len(body["items"]) == 5
