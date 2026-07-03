from datetime import datetime
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field


class PlayerOut(BaseModel):
    id: PydanticObjectId
    queue_number: int
    member_id: PydanticObjectId
    name: str
    phone: str
    paid: bool
    added_at: datetime


class PendingRequestOut(BaseModel):
    id: PydanticObjectId
    member_id: PydanticObjectId
    name: str
    phone: str
    requested_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PydanticObjectId = Field(alias="_id")
    date: datetime
    status: Literal["open", "closed"]
    share_code: str
    fee: float
    revenue: float
    title: str
    notes: str
    location: str
    capacity: int | None
    queue: list[PlayerOut]
    pending: list[PendingRequestOut]


class PaginatedSessions(BaseModel):
    items: list[SessionOut]
    total: int
    page: int
    page_size: int
