from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.core.enums import EntityStatus
from app.core.cache import redis
from app.core.config import settings
from app.services.auth_service import invalidate_rbac_cache

async def list_permissions_for_user(db: AsyncSession, user_id: str) -> set[str]:
    try:
        cache_key = f"rbac:perms:{user_id}"
        if redis:
            cached = await redis.smembers(cache_key)
            if cached:
                return set(cached)

        # 1 query join thay vì 2-3 query
        stmt = (
            select(Permission.code)
            .select_from(UserRole)
            .join(RolePermission, RolePermission.role_id == UserRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(UserRole.user_id == user_id, Permission.status == EntityStatus.ACTIVE)
        )
        perms = (await db.execute(stmt)).scalars().all()
        perms_set = set(perms)

        if redis:
            if perms_set:
                await redis.sadd(cache_key, *list(perms_set))
                await redis.expire(cache_key, settings.RBAC_CACHE_TTL_SECONDS)
            else:
                # cache empty to avoid stampede
                await redis.setex(cache_key, settings.RBAC_CACHE_TTL_SECONDS, "")

        return perms_set
    except Exception as e:
        raise ValueError(f"LIST_PERMISSIONS_FOR_USER_FAILED: {str(e)}") from e

async def assign_roles_to_user(db: AsyncSession, user_id: str, role_codes: list[str]) -> None:
    try:
        roles = (await db.execute(select(Role).where(Role.code.in_(role_codes), Role.status == EntityStatus.ACTIVE))).scalars().all()

        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        for r in roles:
            db.add(UserRole(user_id=user_id, role_id=r.id))
        await db.commit()

        await invalidate_rbac_cache(user_id)
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("ASSIGN_ROLES_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ASSIGN_ROLES_TO_USER_FAILED: {str(e)}") from e
    
async def assign_permissions_to_role(db: AsyncSession, role_code: str, permission_codes: list[str]) -> None:
    try:
        role = (await db.execute(select(Role).where(Role.code == role_code))).scalar_one_or_none()
        if not role:
            raise ValueError("ROLE_NOT_FOUND")
            
        perms = (await db.execute(select(Permission).where(Permission.code.in_(permission_codes)))).scalars().all()

        await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
        for p in perms:
            db.add(RolePermission(role_id=role.id, permission_id=p.id))
        await db.commit()
    except ValueError:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise ValueError("ASSIGN_PERMISSIONS_INTEGRITY_ERROR") from e
    except Exception as e:
        await db.rollback()
        raise ValueError(f"ASSIGN_PERMISSIONS_TO_ROLE_FAILED: {str(e)}") from e