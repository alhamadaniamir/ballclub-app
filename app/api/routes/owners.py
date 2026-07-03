import re

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from app.api.deps import require_auth
from app.core.security import hash_password
from app.models.owner import Owner
from app.services.activity import log_activity

router = APIRouter(prefix="/owners", tags=["owners"], dependencies=[Depends(require_auth)])


class OwnerIn(BaseModel):
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""


class OwnerOut(BaseModel):
    id: PydanticObjectId
    username: str
    first_name: str
    last_name: str
    full_name: str
    role: str


def _serialize(owner: Owner) -> OwnerOut:
    full_name = " ".join(part for part in [owner.first_name, owner.last_name] if part)
    return OwnerOut(
        id=owner.id,
        username=owner.username,
        first_name=owner.first_name,
        last_name=owner.last_name,
        full_name=full_name or owner.username,
        role="Owner",
    )


def _validate(username: str, password: str) -> None:
    if len(username.strip()) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")


@router.get("/", response_model=list[OwnerOut])
async def list_owners(search: str | None = Query(default=None)):
    query = {}
    if search:
        pattern = re.escape(search.strip())
        query = {
            "$or": [
                {"username": {"$regex": pattern, "$options": "i"}},
                {"first_name": {"$regex": pattern, "$options": "i"}},
                {"last_name": {"$regex": pattern, "$options": "i"}},
            ]
        }
    owners = await Owner.find(query).sort("+username").to_list()
    return [_serialize(o) for o in owners]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OwnerOut)
async def create_owner(payload: OwnerIn):
    _validate(payload.username, payload.password)

    owner = Owner(
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
    )
    try:
        await owner.insert()
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An owner with this username already exists")
    await log_activity(f"Created owner account '{owner.username}'")
    return _serialize(owner)


@router.delete("/{owner_id}")
async def delete_owner(owner_id: PydanticObjectId):
    owner = await Owner.get(owner_id)
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    if await Owner.find_all().count() <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last remaining owner")

    await owner.delete()
    await log_activity(f"Removed owner account '{owner.username}'")
    return {"message": "Owner deleted"}
