"""Auth router (placeholder)"""
from fastapi import APIRouter
from ..schemas.auth import LoginSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/ping")
def ping():
    return {"ping": "pong"}


@router.post("/login")
def login(payload: LoginSchema):
    return {"access_token": "token", "token_type": "bearer"}
