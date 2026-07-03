from fastapi import APIRouter, Depends

from app.api.deps import require_auth
from app.models.activity import Activity
from app.models.member import Member
from app.models.owner import Owner
from app.models.session import Session
from app.schemas.dashboard import ActivityOut, ActiveSessionSummary, DashboardOut, RecentSessionSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_auth)])


@router.get("/", response_model=DashboardOut)
async def get_dashboard():
    total_members = await Member.find_all().count()
    total_owners = await Owner.find_all().count()
    total_sessions = await Session.find_all().count()
    open_sessions = await Session.find({"status": "open"}).count()
    closed_sessions = await Session.find({"status": "closed"}).count()

    active_session = None
    open_session = await Session.find_one({"status": "open"})
    if open_session:
        active_session = ActiveSessionSummary(
            id=open_session.id,
            share_code=open_session.share_code,
            queue_count=len(open_session.queue),
            paid_count=sum(1 for p in open_session.queue if p.paid),
            pending_count=len(open_session.pending),
        )

    all_sessions = await Session.find_all().to_list()
    total_revenue = sum(sum(1 for p in s.queue if p.paid) * s.fee for s in all_sessions)

    recent = await Session.find({"status": "closed"}).sort("-date").limit(5).to_list()
    recent_sessions = [
        RecentSessionSummary(
            id=s.id,
            date=s.date,
            status=s.status,
            title=s.title,
            queue_count=len(s.queue),
            paid_count=sum(1 for p in s.queue if p.paid),
            fee=s.fee,
            revenue=sum(1 for p in s.queue if p.paid) * s.fee,
        )
        for s in recent
    ]

    activities = await Activity.find_all().sort("-created_at").limit(10).to_list()
    recent_activity = [ActivityOut(id=a.id, description=a.description, created_at=a.created_at) for a in activities]

    return DashboardOut(
        total_members=total_members,
        total_owners=total_owners,
        total_sessions=total_sessions,
        open_sessions=open_sessions,
        closed_sessions=closed_sessions,
        total_revenue=total_revenue,
        active_session=active_session,
        recent_sessions=recent_sessions,
        recent_activity=recent_activity,
    )
