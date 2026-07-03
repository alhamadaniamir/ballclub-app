from beanie import PydanticObjectId
from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from app.api.deps import require_auth
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.core.validation import validate_name
from app.models.owner import Owner

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class MeOut(BaseModel):
    id: PydanticObjectId
    username: str
    first_name: str
    last_name: str


class ProfileUpdateIn(BaseModel):
    username: str
    first_name: str = ""
    last_name: str = ""


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


async def _get_owner_from_token(token_payload: dict) -> Owner:
    owner = await Owner.get(PydanticObjectId(token_payload["sub"]))
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return owner


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest):
    owner = await Owner.find_one({"username": payload.username})
    if not owner or not verify_password(payload.password, owner.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token({"role": "owner", "sub": str(owner.id), "username": owner.username})
    return LoginResponse(token=token)


@router.get("/me", response_model=MeOut)
async def get_me(token_payload: dict = Depends(require_auth)):
    owner = await _get_owner_from_token(token_payload)
    return MeOut(id=owner.id, username=owner.username, first_name=owner.first_name, last_name=owner.last_name)


@router.patch("/me/profile", response_model=MeOut)
async def update_profile(payload: ProfileUpdateIn, token_payload: dict = Depends(require_auth)):
    if len(payload.username.strip()) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters.")
    if payload.first_name and not validate_name(payload.first_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid first name. Must be 2-100 characters.")
    if payload.last_name and not validate_name(payload.last_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid last name. Must be 2-100 characters.")

    owner = await _get_owner_from_token(token_payload)
    owner.username = payload.username.strip()
    owner.first_name = payload.first_name
    owner.last_name = payload.last_name
    try:
        await owner.save()
    except (DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An owner with this username already exists")
    return MeOut(id=owner.id, username=owner.username, first_name=owner.first_name, last_name=owner.last_name)


@router.patch("/me")
async def update_me(payload: ChangePasswordIn, token_payload: dict = Depends(require_auth)):
    owner = await _get_owner_from_token(token_payload)
    if not verify_password(payload.current_password, owner.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")

    owner.password_hash = hash_password(payload.new_password)
    await owner.save()
    return {"message": "Password updated"}
