"""RBAC router (placeholder)"""
from fastapi import APIRouter

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/roles")
def list_roles():
    return [{"name": "user"}, {"name": "admin"}]
