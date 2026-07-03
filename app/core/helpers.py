import secrets
import string

from app.models.session import Player


def generate_share_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def get_next_queue_number(queue: list[Player]) -> int:
    if not queue:
        return 1
    return max(p.queue_number for p in queue) + 1
