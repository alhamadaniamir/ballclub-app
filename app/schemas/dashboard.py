from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel


class ActiveSessionSummary(BaseModel):
    id: PydanticObjectId
    share_code: str
    queue_count: int
    paid_count: int
    pending_count: int


class RecentSessionSummary(BaseModel):
    id: PydanticObjectId
    date: datetime
    status: str
    title: str
    queue_count: int
    paid_count: int
    fee: float
    revenue: float


class ActivityOut(BaseModel):
    id: PydanticObjectId
    description: str
    created_at: datetime


class DashboardOut(BaseModel):
    total_members: int
    total_owners: int
    total_sessions: int
    open_sessions: int
    closed_sessions: int
    total_revenue: float
    active_session: ActiveSessionSummary | None
    recent_sessions: list[RecentSessionSummary]
    recent_activity: list[ActivityOut]
