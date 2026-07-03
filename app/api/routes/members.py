import csv
import io
import re

from beanie import PydanticObjectId
from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from app.api.deps import require_auth
from app.core.validation import validate_name, validate_phone
from app.models.member import Member
from app.schemas.member import MemberHistoryOut
from app.services.activity import log_activity
from app.services.members import get_member_history

router = APIRouter(prefix="/members", tags=["members"], dependencies=[Depends(require_auth)])


class MemberIn(BaseModel):
    first_name: str
    middle_name: str = ""
    last_name: str
    phone: str = ""


class MemberUpdate(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


def _validate(first_name: str | None, middle_name: str | None, last_name: str | None, phone: str | None) -> None:
    if first_name is not None and not validate_name(first_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid first name. Must be 2-100 characters.")
    if last_name is not None and not validate_name(last_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid last name. Must be 2-100 characters.")
    if middle_name and not validate_name(middle_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid middle name. Must be 2-100 characters.")
    if phone is not None and phone and not validate_phone(phone):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone. Must be 10-15 digits.")


@router.get("/")
async def list_members(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query = {
            "$or": [
                {"first_name": {"$regex": pattern, "$options": "i"}},
                {"last_name": {"$regex": pattern, "$options": "i"}},
                {"phone": {"$regex": pattern, "$options": "i"}},
            ]
        }
    total = await Member.find(query).count()
    items = (
        await Member.find(query).sort("+first_name").skip((page - 1) * page_size).limit(page_size).to_list()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/export")
async def export_members():
    members = await Member.find_all().sort("+first_name").to_list()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["first_name", "middle_name", "last_name", "phone", "date_joined"])
    for m in members:
        writer.writerow([m.first_name, m.middle_name, m.last_name, m.phone, m.date_joined.date()])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="members.csv"'},
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_member(payload: MemberIn):
    _validate(payload.first_name, payload.middle_name, payload.last_name, payload.phone)

    member = Member(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        phone=payload.phone or "",
    )
    try:
        await member.insert()
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A member with this phone already exists")
    await log_activity(f"Added member {member.full_name}")
    return member


@router.get("/{member_id}/history", response_model=MemberHistoryOut)
async def member_history(member_id: PydanticObjectId):
    member = await Member.get(member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return await get_member_history(member)


@router.patch("/{member_id}")
async def update_member(member_id: PydanticObjectId, payload: MemberUpdate):
    _validate(payload.first_name, payload.middle_name, payload.last_name, payload.phone)

    member = await Member.get(member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if payload.first_name is not None:
        member.first_name = payload.first_name
    if payload.middle_name is not None:
        member.middle_name = payload.middle_name
    if payload.last_name is not None:
        member.last_name = payload.last_name
    if payload.phone is not None:
        member.phone = payload.phone
    try:
        await member.save()
    except (DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A member with this phone already exists")
    return member


@router.delete("/{member_id}")
async def delete_member(member_id: PydanticObjectId):
    member = await Member.get(member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await member.delete()
    await log_activity(f"Removed member {member.full_name}")
    return {"message": "Member deleted"}
