from datetime import datetime, timezone

from beanie import Document
from pydantic import Field
from pymongo import DESCENDING, IndexModel


class Activity(Document):
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "activities"
        indexes = [IndexModel([("created_at", DESCENDING)])]
