import pytest

pytestmark = pytest.mark.asyncio


async def test_dashboard_empty_state(client, auth_headers):
    res = await client.get("/api/dashboard/", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_members"] == 0
    assert data["total_sessions"] == 0
    assert data["active_session"] is None
    assert data["recent_sessions"] == []
    assert data["recent_activity"] == []
    assert data["total_owners"] == 1


async def test_dashboard_reflects_activity(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    await client.post(f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "Walk", "last_name": "In"})

    await client.post(
        f"/api/public/session/{session['share_code']}/join",
        json={"first_name": "John", "last_name": "Doe", "phone": "5551234567"},
    )

    res = await client.get("/api/dashboard/", headers=auth_headers)
    data = res.json()
    assert data["total_sessions"] == 1
    assert data["open_sessions"] == 1
    assert data["closed_sessions"] == 0
    assert data["active_session"]["queue_count"] == 1
    assert data["active_session"]["pending_count"] == 1
    assert data["total_members"] == 2  # one from the walk-in, one from the join request
    assert len(data["recent_activity"]) >= 2  # session started + walk-in added + join request

    await client.patch(f"/api/sessions/{sid}/close", headers=auth_headers)

    res = await client.get("/api/dashboard/", headers=auth_headers)
    data = res.json()
    assert data["active_session"] is None
    assert data["closed_sessions"] == 1
    assert len(data["recent_sessions"]) == 1
    assert data["recent_sessions"][0]["queue_count"] == 1
    assert data["recent_activity"][0]["description"] == "Closed a session"


async def test_dashboard_total_revenue(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    await client.patch(f"/api/sessions/{sid}/fee", headers=auth_headers, json={"fee": 25})
    walk = (
        await client.post(
            f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "Rev", "last_name": "Enue"}
        )
    ).json()
    await client.patch(f"/api/sessions/{sid}/players/{walk['queue'][0]['id']}", headers=auth_headers)

    res = await client.get("/api/dashboard/", headers=auth_headers)
    assert res.json()["total_revenue"] == 25.0


async def test_dashboard_requires_auth(client):
    res = await client.get("/api/dashboard/")
    assert res.status_code == 401
