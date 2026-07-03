from app.models.member import Member
from app.models.session import Session
from app.schemas.session import PendingRequestOut, PlayerOut, SessionOut


async def serialize_session(session: Session, search: str | None = None) -> SessionOut:
    member_ids = {p.member_id for p in session.queue} | {r.member_id for r in session.pending}
    members: dict = {}
    if member_ids:
        docs = await Member.find({"_id": {"$in": list(member_ids)}}).to_list()
        members = {m.id: m for m in docs}

    def resolve(member_id):
        member = members.get(member_id)
        return (member.full_name, member.phone) if member else ("Unknown member", "")

    queue_out = []
    for player in session.queue:
        name, phone = resolve(player.member_id)
        queue_out.append(
            PlayerOut(
                id=player.id,
                queue_number=player.queue_number,
                member_id=player.member_id,
                name=name,
                phone=phone,
                paid=player.paid,
                added_at=player.added_at,
            )
        )

    pending_out = []
    for request in session.pending:
        name, phone = resolve(request.member_id)
        pending_out.append(
            PendingRequestOut(
                id=request.id,
                member_id=request.member_id,
                name=name,
                phone=phone,
                requested_at=request.requested_at,
            )
        )

    revenue = sum(1 for p in session.queue if p.paid) * session.fee

    if search:
        needle = search.strip().lower()
        queue_out = [p for p in queue_out if needle in p.name.lower()]
        pending_out = [r for r in pending_out if needle in r.name.lower()]

    return SessionOut(
        _id=session.id,
        date=session.date,
        status=session.status,
        share_code=session.share_code,
        fee=session.fee,
        revenue=revenue,
        title=session.title,
        notes=session.notes,
        location=session.location,
        capacity=session.capacity,
        queue=queue_out,
        pending=pending_out,
    )
