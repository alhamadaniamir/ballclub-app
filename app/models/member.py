from datetime import datetime, timezone

from beanie import Document
from pydantic import Field, computed_field
from pymongo import ASCENDING, IndexModel


class Member(Document):
    first_name: str
    middle_name: str = ""
    last_name: str
    phone: str = ""
    date_joined: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def full_name(self) -> str:
        return " ".join(part for part in [self.first_name, self.middle_name, self.last_name] if part)

    class Settings:
        name = "members"
        indexes = [
            IndexModel(
                [("phone", ASCENDING)],
                unique=True,
                partialFilterExpression={"phone": {"$gt": ""}},
            ),
        ]
