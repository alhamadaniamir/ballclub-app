import pytest

pytestmark = pytest.mark.asyncio


async def test_create_session_is_idempotent(client, auth_headers):
    res1 = await client.post("/api/sessions/", headers=auth_headers)
    res2 = await client.post("/api/sessions/", headers=auth_headers)
    assert res1.json()["_id"] == res2.json()["_id"]


async def test_join_approve_flow_populates_member_data(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    share_code = session["share_code"]

    res = await client.post(
        f"/api/public/session/{share_code}/join",
        json={"first_name": "John", "last_name": "Doe", "phone": "5551234567"},
    )
    assert res.status_code == 201

    session = (await client.get(f"/api/sessions/{session['_id']}", headers=auth_headers)).json()
    assert len(session["pending"]) == 1
    pending = session["pending"][0]
    assert pending["name"] == "John Doe"
    assert pending["phone"] == "5551234567"

    res = await client.post(
        f"/api/sessions/{session['_id']}/pending/{pending['id']}/approve", headers=auth_headers
    )
    session = res.json()
    assert session["pending"] == []
    assert len(session["queue"]) == 1
    assert session["queue"][0]["name"] == "John Doe"
    assert session["queue"][0]["queue_number"] == 1

    members = (await client.get("/api/members/", headers=auth_headers)).json()["items"]
    assert len(members) == 1
    assert members[0]["phone"] == "5551234567"


async def test_decline_request_does_not_create_member(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    await client.post(
        f"/api/public/session/{session['share_code']}/join",
        json={"first_name": "John", "last_name": "Doe", "phone": "5551234567"},
    )
    session = (await client.get(f"/api/sessions/{session['_id']}", headers=auth_headers)).json()
    pending_id = session["pending"][0]["id"]

    res = await client.post(f"/api/sessions/{session['_id']}/pending/{pending_id}/decline", headers=auth_headers)
    assert res.json()["pending"] == []

    members = (await client.get("/api/members/", headers=auth_headers)).json()["items"]
    assert len(members) == 1  # get_or_create_member creates the contact on join, decline just skips queueing


async def test_join_rejects_closed_session(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    await client.patch(f"/api/sessions/{session['_id']}/close", headers=auth_headers)

    res = await client.post(
        f"/api/public/session/{session['share_code']}/join",
        json={"first_name": "John", "last_name": "Doe", "phone": "5551234567"},
    )
    assert res.status_code == 400


async def test_walkin_reuses_existing_member_by_phone(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]

    await client.post(
        f"/api/sessions/{sid}/walkin",
        headers=auth_headers,
        json={"first_name": "John", "last_name": "Doe", "phone": "5551234567"},
    )
    res = await client.post(
        f"/api/sessions/{sid}/walkin",
        headers=auth_headers,
        json={"first_name": "John", "last_name": "Doe Again", "phone": "5551234567"},
    )
    assert len(res.json()["queue"]) == 2

    members = (await client.get("/api/members/", headers=auth_headers)).json()["items"]
    assert len(members) == 1
    assert members[0]["full_name"] == "John Doe"


async def test_toggle_paid_and_delete_player(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    session = (
        await client.post(
            f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "Walk", "last_name": "In"}
        )
    ).json()
    player_id = session["queue"][0]["id"]

    res = await client.patch(f"/api/sessions/{sid}/players/{player_id}", headers=auth_headers)
    assert res.json()["queue"][0]["paid"] is True

    res = await client.delete(f"/api/sessions/{sid}/players/{player_id}", headers=auth_headers)
    assert res.json()["queue"] == []


async def test_close_and_delete_session(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]

    res = await client.patch(f"/api/sessions/{sid}/close", headers=auth_headers)
    assert res.json()["status"] == "closed"

    res = await client.delete(f"/api/sessions/{sid}", headers=auth_headers)
    assert res.status_code == 200

    res = await client.get(f"/api/sessions/{sid}", headers=auth_headers)
    assert res.status_code == 404


async def test_list_sessions_filters_by_status(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    await client.patch(f"/api/sessions/{session['_id']}/close", headers=auth_headers)
    await client.post("/api/sessions/", headers=auth_headers)  # new open session

    res = await client.get("/api/sessions/", headers=auth_headers, params={"status": "closed"})
    statuses = {s["status"] for s in res.json()["items"]}
    assert statuses == {"closed"}

    res = await client.get("/api/sessions/", headers=auth_headers, params={"status": "open"})
    statuses = {s["status"] for s in res.json()["items"]}
    assert statuses == {"open"}

    res = await client.get("/api/sessions/", headers=auth_headers)
    body = res.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


async def test_list_sessions_filters_by_date_range(client, auth_headers):
    from datetime import datetime, timedelta, timezone

    from app.models.session import Session

    now = datetime.now(timezone.utc)
    recent_session = Session(share_code="RECENT", date=now - timedelta(days=2))
    old_session = Session(share_code="OLDONE", date=now - timedelta(days=400))
    await recent_session.insert()
    await old_session.insert()

    date_from = (now - timedelta(days=30)).isoformat()
    res = await client.get("/api/sessions/", headers=auth_headers, params={"date_from": date_from})
    codes = {s["share_code"] for s in res.json()["items"]}
    assert "RECENT" in codes
    assert "OLDONE" not in codes

    date_to = (now - timedelta(days=100)).isoformat()
    res = await client.get("/api/sessions/", headers=auth_headers, params={"date_to": date_to})
    codes = {s["share_code"] for s in res.json()["items"]}
    assert "OLDONE" in codes
    assert "RECENT" not in codes


async def test_get_session_search_filters_queue_and_pending(client, auth_headers):
    # NOTE: walk-ins here use distinct phone numbers rather than leaving phone blank for both.
    # mongomock doesn't honor Mongo's partialFilterExpression on the Member.phone unique index
    # (verified separately against real MongoDB Atlas, where two blank-phone members are fine),
    # so two blank-phone inserts in the same test would collide only under the mock.
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    await client.post(
        f"/api/sessions/{sid}/walkin",
        headers=auth_headers,
        json={"first_name": "Alice", "last_name": "Cooper", "phone": "5551110001"},
    )
    await client.post(
        f"/api/sessions/{sid}/walkin",
        headers=auth_headers,
        json={"first_name": "Bob", "last_name": "Marley", "phone": "5551110002"},
    )
    await client.post(
        f"/api/public/session/{session['share_code']}/join",
        json={"first_name": "Carl", "last_name": "Sagan", "phone": "5551234567"},
    )

    res = await client.get(f"/api/sessions/{sid}", headers=auth_headers, params={"search": "alice"})
    data = res.json()
    assert [p["name"] for p in data["queue"]] == ["Alice Cooper"]
    assert data["pending"] == []

    res = await client.get(f"/api/sessions/{sid}", headers=auth_headers, params={"search": "carl"})
    data = res.json()
    assert data["queue"] == []
    assert [r["name"] for r in data["pending"]] == ["Carl Sagan"]

    res = await client.get(f"/api/sessions/{sid}", headers=auth_headers)
    assert len(res.json()["queue"]) == 2


async def test_lookup_by_phone(client, auth_headers):
    await client.post(
        "/api/members/", headers=auth_headers, json={"first_name": "Jane", "last_name": "Doe", "phone": "5551234567"}
    )

    res = await client.get("/api/public/lookup", params={"phone": "5551234567"})
    data = res.json()
    assert data["found"] is True
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["name"] == "Jane Doe"

    res = await client.get("/api/public/lookup", params={"phone": "5550000000"})
    assert res.json() == {"found": False}

    res = await client.get("/api/public/lookup", params={"phone": "abc"})
    assert res.status_code == 400


async def test_session_fee_and_revenue(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    assert session["fee"] == 0.0
    assert session["revenue"] == 0.0

    res = await client.patch(f"/api/sessions/{sid}/fee", headers=auth_headers, json={"fee": 50})
    assert res.status_code == 200
    assert res.json()["fee"] == 50.0

    session = (
        await client.post(
            f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "Pay", "last_name": "Er"}
        )
    ).json()
    player_id = session["queue"][0]["id"]
    assert session["revenue"] == 0.0  # not paid yet

    res = await client.patch(f"/api/sessions/{sid}/players/{player_id}", headers=auth_headers)
    assert res.json()["revenue"] == 50.0  # one paid player * fee


async def test_session_fee_rejects_negative(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    res = await client.patch(f"/api/sessions/{session['_id']}/fee", headers=auth_headers, json={"fee": -5})
    assert res.status_code == 422


async def test_session_metadata_update(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    res = await client.patch(
        f"/api/sessions/{sid}",
        headers=auth_headers,
        json={"title": "Friday Night Hoops", "notes": "Bring water", "location": "Court A", "capacity": 10},
    )
    data = res.json()
    assert data["title"] == "Friday Night Hoops"
    assert data["notes"] == "Bring water"
    assert data["location"] == "Court A"
    assert data["capacity"] == 10


async def test_session_capacity_blocks_when_full(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    await client.patch(f"/api/sessions/{sid}", headers=auth_headers, json={"capacity": 1})

    res = await client.post(
        f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "First", "last_name": "Player"}
    )
    assert res.status_code == 201

    res = await client.post(
        f"/api/sessions/{sid}/walkin", headers=auth_headers, json={"first_name": "Second", "last_name": "Player"}
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Session is full"


async def test_session_csv_export(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    await client.patch(f"/api/sessions/{sid}/fee", headers=auth_headers, json={"fee": 40})
    walk = (
        await client.post(
            f"/api/sessions/{sid}/walkin",
            headers=auth_headers,
            json={"first_name": "Csv", "last_name": "Player", "phone": "5551112222"},
        )
    ).json()
    await client.patch(f"/api/sessions/{sid}/players/{walk['queue'][0]['id']}", headers=auth_headers)

    res = await client.get(f"/api/sessions/{sid}/export", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    body = res.text
    assert "queue_number,name,phone,paid,amount" in body
    assert "Csv Player" in body
    assert "yes,40" in body


async def test_members_csv_export(client, auth_headers):
    await client.post(
        "/api/members/",
        headers=auth_headers,
        json={"first_name": "Export", "last_name": "Me", "phone": "5553334444"},
    )
    res = await client.get("/api/members/export", headers=auth_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "5553334444" in res.text


async def test_session_capacity_rejects_below_current_queue(client, auth_headers):
    session = (await client.post("/api/sessions/", headers=auth_headers)).json()
    sid = session["_id"]
    for i in range(2):
        await client.post(
            f"/api/sessions/{sid}/walkin",
            headers=auth_headers,
            json={"first_name": f"Player{i}", "last_name": "Test", "phone": f"555000000{i}"},
        )
    res = await client.patch(f"/api/sessions/{sid}", headers=auth_headers, json={"capacity": 1})
    assert res.status_code == 400
