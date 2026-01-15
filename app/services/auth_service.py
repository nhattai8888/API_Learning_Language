"""Authentication service placeholder"""
from typing import Optional


def authenticate(username: str, password: str) -> Optional[dict]:
    # placeholder logic
    if username and password:
        return {"username": username}
    return None
