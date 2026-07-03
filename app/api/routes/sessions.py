import csv
import io
from datetime import datetime
from typing import Literal

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import require_auth
from app.core.helpers import generate_share_code, get_next_queue_number
from app.core.validation import validate_name, validate_phone
from app.models.session import Player, Session
from app.schemas.session import PaginatedSessions, SessionOut
from app.services.activity import log_activity
from app.services.members import get_or_create_member
from app.services.sessions import serialize_session

router = APIRouter(prefix="/sessions", tags=["sessions"], dependencies=[Depends(require_auth)])


class WalkinIn(BaseModel):
    first_name: str
    middle_name: str = ""
    last_name: str
    phone: str = ""


class FeeIn(BaseModel):
    fee: float = Field(ge=0)


class SessionMetaIn(BaseModel):
    title: str | None = None
    notes: str | None = None
    location: str | None = None
    capacity: int | None = None


def _assert_not_full(session: Session) -> None:
    if session.capacity is not None and len(session.queue) >= session.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is full")


def _get_or_404(session, item_id, items_attr):
    items = getattr(session, items_attr)
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


async def _get_session_or_404(session_id: PydanticObjectId) -> Session:
    session = await Session.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.get("/", response_model=PaginatedSessions)
async def list_sessions(
    status_filter: Literal["open", "closed"] | None = Query(default=None, alias="status"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query: dict = {}
    if status_filter:
        query["status"] = status_filter
    if date_from or date_to:
        date_query: dict = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        query["date"] = date_query
    total = await Session.find(query).count()
    sessions = await Session.find(query).sort("-date").skip((page - 1) * page_size).limit(page_size).to_list()
    items = [await serialize_session(s) for s in sessions]
    return PaginatedSessions(items=items, total=total, page=page, page_size=page_size)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SessionOut)
async def create_session():
    open_session = await Session.find_one({"status": "open"})
    if open_session:
        return await serialize_session(open_session)

    session = Session(share_code=generate_share_code())
    await session.insert()
    await log_activity("Started a new session")
    return await serialize_session(session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: PydanticObjectId, search: str | None = Query(default=None)):
    session = await _get_session_or_404(session_id)
    return await serialize_session(session, search=search)


@router.get("/{session_id}/export")
async def export_session(session_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    data = await serialize_session(session)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["queue_number", "name", "phone", "paid", "amount"])
    for player in data.queue:
        amount = session.fee if player.paid else 0
        writer.writerow([player.queue_number, player.name, player.phone, "yes" if player.paid else "no", f"{amount:g}"])

    filename = f"session-{session.date.date()}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{session_id}/close", response_model=SessionOut)
async def close_session(session_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    session.status = "closed"
    await session.save()
    await log_activity("Closed a session")
    return await serialize_session(session)


@router.patch("/{session_id}/fee", response_model=SessionOut)
async def set_fee(session_id: PydanticObjectId, payload: FeeIn):
    session = await _get_session_or_404(session_id)
    session.fee = payload.fee
    await session.save()
    await log_activity(f"Set session fee to {payload.fee:g}")
    return await serialize_session(session)


@router.patch("/{session_id}", response_model=SessionOut)
async def update_session_meta(session_id: PydanticObjectId, payload: SessionMetaIn):
    session = await _get_session_or_404(session_id)
    fields = payload.model_fields_set

    if "title" in fields:
        session.title = (payload.title or "").strip()
    if "notes" in fields:
        session.notes = (payload.notes or "").strip()
    if "location" in fields:
        session.location = (payload.location or "").strip()
    if "capacity" in fields:
        if payload.capacity is None:
            session.capacity = None
        else:
            if payload.capacity < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capacity must be at least 1.")
            if payload.capacity < len(session.queue):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Capacity cannot be below the current number of players.",
                )
            session.capacity = payload.capacity

    await session.save()
    await log_activity("Updated session details")
    return await serialize_session(session)


@router.delete("/{session_id}")
async def delete_session(session_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    await session.delete()
    await log_activity("Deleted a session")
    return {"message": "Session deleted"}


@router.post("/{session_id}/walkin", status_code=status.HTTP_201_CREATED, response_model=SessionOut)
async def add_walkin(session_id: PydanticObjectId, payload: WalkinIn):
    if not payload.first_name or not payload.last_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required")
    if not validate_name(payload.first_name) or not validate_name(payload.last_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name. Must be 2-100 characters.")
    if payload.middle_name and not validate_name(payload.middle_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid middle name. Must be 2-100 characters.")
    if payload.phone and not validate_phone(payload.phone):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone. Must be 10-15 digits.")

    session = await _get_session_or_404(session_id)
    if session.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is closed")
    _assert_not_full(session)

    member = await get_or_create_member(
        payload.first_name, payload.last_name, payload.phone or "", middle_name=payload.middle_name
    )
    next_number = get_next_queue_number(session.queue)
    session.queue.append(Player(queue_number=next_number, member_id=member.id))
    await session.save()
    await log_activity(f"Added walk-in {member.full_name} to the queue")
    return await serialize_session(session)


@router.patch("/{session_id}/players/{player_id}", response_model=SessionOut)
async def toggle_paid(session_id: PydanticObjectId, player_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    player = _get_or_404(session, player_id, "queue")
    player.paid = not player.paid
    await session.save()
    return await serialize_session(session)


@router.delete("/{session_id}/players/{player_id}", response_model=SessionOut)
async def delete_player(session_id: PydanticObjectId, player_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    _get_or_404(session, player_id, "queue")
    session.queue = [p for p in session.queue if p.id != player_id]
    await session.save()
    await log_activity("Removed a player from the queue")
    return await serialize_session(session)


@router.post("/{session_id}/pending/{request_id}/approve", response_model=SessionOut)
async def approve_request(session_id: PydanticObjectId, request_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    request = _get_or_404(session, request_id, "pending")
    _assert_not_full(session)

    next_number = get_next_queue_number(session.queue)
    session.queue.append(Player(queue_number=next_number, member_id=request.member_id))
    session.pending = [r for r in session.pending if r.id != request_id]
    await session.save()
    await log_activity("Approved a join request")
    return await serialize_session(session)


@router.post("/{session_id}/pending/{request_id}/decline", response_model=SessionOut)
async def decline_request(session_id: PydanticObjectId, request_id: PydanticObjectId):
    session = await _get_session_or_404(session_id)
    _get_or_404(session, request_id, "pending")
    session.pending = [r for r in session.pending if r.id != request_id]
    await session.save()
    await log_activity("Declined a join request")
    return await serialize_session(session)
