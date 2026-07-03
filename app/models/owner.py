from datetime import datetime, timezone

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Owner(Document):
    username: str
    password_hash: str
    first_name: str = ""
    last_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "owners"
        indexes = [
            IndexModel([("username", ASCENDING)], unique=True),
        ]
