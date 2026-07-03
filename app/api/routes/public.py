from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.core.rate_limit import limiter
from app.core.validation import validate_name, validate_phone
from app.models.member import Member
from app.models.session import PendingRequest, Session
from app.services.activity import log_activity
from app.services.members import get_or_create_member

router = APIRouter(prefix="/public", tags=["public"])


class JoinIn(BaseModel):
    first_name: str
    middle_name: str = ""
    last_name: str
    phone: str


@router.get("/session/{share_code}")
async def get_session_status(share_code: str):
    session = await Session.find_one({"share_code": share_code})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found or expired")
    return {"date": session.date, "status": session.status}


@router.get("/lookup")
async def lookup_member(phone: str | None = Query(default=None)):
    if not phone:
        return {"found": False}
    if not validate_phone(phone):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone format")

    member = await Member.find_one({"phone": phone})
    if member:
        return {
            "found": True,
            "first_name": member.first_name,
            "middle_name": member.middle_name,
            "last_name": member.last_name,
            "name": member.full_name,
        }
    return {"found": False}


@router.post("/session/{share_code}/join", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def join_session(request: Request, share_code: str, payload: JoinIn):
    if not payload.first_name or not payload.last_name or not payload.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and phone are required")
    if not validate_name(payload.first_name) or not validate_name(payload.last_name) or not validate_phone(payload.phone):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid name or phone format")
    if payload.middle_name and not validate_name(payload.middle_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid middle name format")

    session = await Session.find_one({"share_code": share_code})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found or expired")
    if session.status == "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This session is closed")

    member = await get_or_create_member(
        payload.first_name, payload.last_name, payload.phone, middle_name=payload.middle_name
    )
    session.pending.append(PendingRequest(member_id=member.id))
    await session.save()
    await log_activity(f"{member.full_name} requested to join a session")
    return {"message": "Request sent. Wait for the owner to approve you."}
