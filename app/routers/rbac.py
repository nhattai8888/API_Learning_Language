from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.schemas.common import ApiResponse
from app.schemas.rbac import (
    RoleCreate, PermissionCreate, AssignRoleRequest, AssignPermissionToRoleRequest,
    RoleOut, PermissionOut
)
from app.models.rbac import Role, Permission
from app.deps import require_permissions
from app.services.rbac_service import assign_roles_to_user, assign_permissions_to_role

router = APIRouter(prefix="/rbac", tags=["rbac"])

@router.post("/roles", dependencies=[Depends(require_permissions(["ROLE_MANAGE"]))], response_model=ApiResponse[RoleOut])
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)):
    role = Role(code=payload.code, name=payload.name)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return ApiResponse(data=RoleOut(id=str(role.id), code=role.code, name=role.name, status=role.status.value), message="Created")

@router.get("/roles", dependencies=[Depends(require_permissions(["ROLE_MANAGE"]))], response_model=ApiResponse[list[RoleOut]])
async def list_roles(db: AsyncSession = Depends(get_db)):
    roles = (await db.execute(select(Role))).scalars().all()
    data = [RoleOut(id=str(r.id), code=r.code, name=r.name, status=r.status.value) for r in roles]
    return ApiResponse(data=data)

@router.post("/permissions", dependencies=[Depends(require_permissions(["ROLE_MANAGE"]))], response_model=ApiResponse[PermissionOut])
async def create_permission(payload: PermissionCreate, db: AsyncSession = Depends(get_db)):
    p = Permission(code=payload.code, module=payload.module, description=payload.description)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return ApiResponse(data=PermissionOut(id=str(p.id), code=p.code, module=p.module, description=p.description, status=p.status.value), message="Created")

@router.get("/permissions", dependencies=[Depends(require_permissions(["ROLE_MANAGE"]))], response_model=ApiResponse[list[PermissionOut]])
async def list_permissions(db: AsyncSession = Depends(get_db)):
    perms = (await db.execute(select(Permission))).scalars().all()
    data = [PermissionOut(id=str(p.id), code=p.code, module=p.module, description=p.description, status=p.status.value) for p in perms]
    return ApiResponse(data=data)

@router.post("/assign-roles", dependencies=[Depends(require_permissions(["USER_MANAGE"]))], response_model=ApiResponse[dict])
async def assign_roles(payload: AssignRoleRequest, db: AsyncSession = Depends(get_db)):
    await assign_roles_to_user(db, payload.user_id, payload.role_codes)
    return ApiResponse(data={"user_id": payload.user_id, "roles": payload.role_codes}, message="Assigned")

@router.post("/assign-permissions", dependencies=[Depends(require_permissions(["ROLE_MANAGE"]))], response_model=ApiResponse[dict])
async def assign_permissions(payload: AssignPermissionToRoleRequest, db: AsyncSession = Depends(get_db)):
    await assign_permissions_to_role(db, payload.role_code, payload.permission_codes)
    return ApiResponse(data={"role": payload.role_code, "permissions": payload.permission_codes}, message="Assigned")
