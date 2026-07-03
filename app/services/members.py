from pymongo.errors import DuplicateKeyError

from app.models.member import Member
from app.models.session import Session
from app.schemas.member import MemberHistoryOut, MemberSessionEntry


async def get_or_create_member(first_name: str, last_name: str, phone: str, middle_name: str = "") -> Member:
    if phone:
        existing = await Member.find_one({"phone": phone})
        if existing:
            return existing

    member = Member(first_name=first_name, middle_name=middle_name, last_name=last_name, phone=phone)
    try:
        await member.insert()
    except DuplicateKeyError:
        if not phone:
            raise
        existing = await Member.find_one({"phone": phone})
        if not existing:
            raise
        return existing
    return member


async def get_member_history(member: Member) -> MemberHistoryOut:
    sessions = await Session.find({"queue.member_id": member.id}).sort("-date").to_list()

    entries: list[MemberSessionEntry] = []
    total_paid = 0
    total_spent = 0.0
    for session in sessions:
        player = next((p for p in session.queue if p.member_id == member.id), None)
        if player is None:
            continue
        amount = session.fee if player.paid else 0.0
        if player.paid:
            total_paid += 1
            total_spent += amount
        entries.append(
            MemberSessionEntry(
                session_id=session.id,
                date=session.date,
                status=session.status,
                title=session.title,
                paid=player.paid,
                amount=amount,
            )
        )

    return MemberHistoryOut(
        id=member.id,
        first_name=member.first_name,
        middle_name=member.middle_name,
        last_name=member.last_name,
        full_name=member.full_name,
        phone=member.phone,
        date_joined=member.date_joined,
        total_sessions=len(entries),
        total_paid=total_paid,
        total_spent=total_spent,
        sessions=entries,
    )
