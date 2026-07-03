import pytest

pytestmark = pytest.mark.asyncio


async def test_member_history_aggregates_sessions(client, auth_headers):
    # A returning member joins two sessions: paid in one (with a fee), unpaid in the other.
    member = (
        await client.post(
            "/api/members/",
            headers=auth_headers,
            json={"first_name": "Reggie", "last_name": "Miller", "phone": "5559998888"},
        )
    ).json()
    member_id = member["_id"]

    # Session 1: fee 30, member paid.
    s1 = (await client.post("/api/sessions/", headers=auth_headers)).json()
    await client.patch(f"/api/sessions/{s1['_id']}/fee", headers=auth_headers, json={"fee": 30})
    s1 = (
        await client.post(
            f"/api/sessions/{s1['_id']}/walkin",
            headers=auth_headers,
            json={"first_name": "Reggie", "last_name": "Miller", "phone": "5559998888"},
        )
    ).json()
    await client.patch(f"/api/sessions/{s1['_id']}/players/{s1['queue'][0]['id']}", headers=auth_headers)
    await client.patch(f"/api/sessions/{s1['_id']}/close", headers=auth_headers)

    # Session 2: no fee, member unpaid.
    s2 = (await client.post("/api/sessions/", headers=auth_headers)).json()
    await client.post(
        f"/api/sessions/{s2['_id']}/walkin",
        headers=auth_headers,
        json={"first_name": "Reggie", "last_name": "Miller", "phone": "5559998888"},
    )

    res = await client.get(f"/api/members/{member_id}/history", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    # mongomock dot-path canary: the {"queue.member_id": id} query must return both sessions.
    assert data["total_sessions"] == 2
    assert data["total_paid"] == 1
    assert data["total_spent"] == 30.0
    assert data["full_name"] == "Reggie Miller"
    # Sorted by date desc; both entries present with correct amounts.
    amounts = sorted(entry["amount"] for entry in data["sessions"])
    assert amounts == [0.0, 30.0]


async def test_member_history_404_for_unknown(client, auth_headers):
    res = await client.get("/api/members/507f1f77bcf86cd799439011/history", headers=auth_headers)
    assert res.status_code == 404
