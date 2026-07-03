from datetime import datetime, timezone
from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel


class Player(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    queue_number: int
    member_id: PydanticObjectId
    paid: bool = False
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PendingRequest(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    member_id: PydanticObjectId
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Session(Document):
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["open", "closed"] = "open"
    share_code: str
    fee: float = 0.0
    title: str = ""
    notes: str = ""
    location: str = ""
    capacity: int | None = None
    queue: list[Player] = []
    pending: list[PendingRequest] = []

    class Settings:
        name = "sessions"
        indexes = [
            IndexModel([("share_code", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("date", ASCENDING)]),
        ]
