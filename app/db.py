from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.activity import Activity
from app.models.member import Member
from app.models.owner import Owner
from app.models.session import Session


async def init_db() -> None:
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client[settings.MONGO_DB_NAME],
        document_models=[Member, Session, Owner, Activity],
    )
    await _bootstrap_owner()


async def _bootstrap_owner() -> None:
    if await Owner.find_one({}):
        return
    if not settings.OWNER_USERNAME or not settings.OWNER_PASSWORD_HASH:
        return
    await Owner(
        username=settings.OWNER_USERNAME,
        password_hash=settings.OWNER_PASSWORD_HASH,
    ).insert()
