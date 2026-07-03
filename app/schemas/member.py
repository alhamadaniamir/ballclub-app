from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel


class MemberSessionEntry(BaseModel):
    session_id: PydanticObjectId
    date: datetime
    status: str
    title: str
    paid: bool
    amount: float


class MemberHistoryOut(BaseModel):
    id: PydanticObjectId
    first_name: str
    middle_name: str
    last_name: str
    full_name: str
    phone: str
    date_joined: datetime
    total_sessions: int
    total_paid: int
    total_spent: float
    sessions: list[MemberSessionEntry]
