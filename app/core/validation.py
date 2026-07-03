import re


def validate_name(name: str | None) -> bool:
    if not name or not isinstance(name, str):
        return False
    length = len(name.strip())
    return 2 <= length <= 100


def validate_phone(phone: str | None) -> bool:
    if not phone or not isinstance(phone, str):
        return False
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15
