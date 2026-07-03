from app.models.activity import Activity


async def log_activity(description: str) -> None:
    await Activity(description=description).insert()
