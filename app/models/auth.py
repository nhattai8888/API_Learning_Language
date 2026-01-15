"""Auth models placeholder"""
from .base import BaseModel


class AuthModel(BaseModel):
    user_id: int = 0
    token: str = ""
