import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.config import settings
from app.core.enums import IdentityType, IdentityStatus
from app.core.security import hash_password_async
from app.models.user import User
from app.models.auth import UserIdentity
from app.models.rbac import Role, Permission, UserRole, RolePermission

SEED_PATH = Path("app/bootstrap/seed_rbac.json")


async def _get_role(db: AsyncSession, code: str) -> Role | None:
    return (await db.execute(select(Role).where(Role.code == code))).scalar_one_or_none()


async def _get_permission(db: AsyncSession, code: str) -> Permission | None:
    return (await db.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()


async def seed_rbac_from_json(db: AsyncSession, seed_path: Path = SEED_PATH) -> None:
    if not seed_path.exists():
        # Không seed nếu thiếu file (idempotent)
        return

    seed = json.loads(seed_path.read_text(encoding="utf-8"))

    # 1) upsert roles
    for r in seed.get("roles", []):
        role = await _get_role(db, r["code"])
        if not role:
            db.add(Role(code=r["code"], name=r["name"]))

    # 2) upsert permissions
    for p in seed.get("permissions", []):
        perm = await _get_permission(db, p["code"])
        if not perm:
            db.add(Permission(code=p["code"], module=p["module"], description=p.get("description")))

    await db.commit()

    # 3) upsert role_permissions
    role_permissions = seed.get("role_permissions", {})
    all_perm_codes = [p["code"] for p in seed.get("permissions", [])]

    for role_code, perm_codes in role_permissions.items():
        role = await _get_role(db, role_code)
        if not role:
            continue

        # clear old mapping (idempotent)
        await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))

        if perm_codes == ["*"]:
            perm_codes_use = all_perm_codes
        else:
            perm_codes_use = perm_codes

        # insert mappings
        perms = (await db.execute(select(Permission).where(Permission.code.in_(perm_codes_use)))).scalars().all()
        for perm in perms:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    await db.commit()


async def ensure_superadmin(db: AsyncSession) -> None:
    """
    Auto create SuperAdmin user if not exists (by email identity).
    Also assigns SUPERADMIN role.
    """
    if not settings.SUPERADMIN_EMAIL or not settings.SUPERADMIN_PASSWORD:
        return

    # Ensure SUPERADMIN role exists
    role = await _get_role(db, "SUPERADMIN")
    if not role:
        role = Role(code="SUPERADMIN", name="Super Admin")
        db.add(role)
        await db.commit()
        await db.refresh(role)

    # Find identity by email
    identity = (await db.execute(
        select(UserIdentity).where(
            UserIdentity.type == IdentityType.EMAIL,
            UserIdentity.value == settings.SUPERADMIN_EMAIL
        )
    )).scalar_one_or_none()

    if identity:
        user_id = identity.user_id
    else:
        # Create user
        user = User(
            display_name=settings.SUPERADMIN_DISPLAY_NAME,
            password_hash=await hash_password_async(settings.SUPERADMIN_PASSWORD),
            mfa_enabled=True,  # superadmin nên bật MFA mặc định
        )
        db.add(user)
        await db.flush()

        # Create email identity verified
        email_identity = UserIdentity(
            user_id=user.id,
            type=IdentityType.EMAIL,
            value=settings.SUPERADMIN_EMAIL,
            status=IdentityStatus.VERIFIED,
            is_primary=True,
        )
        db.add(email_identity)

        # Optional phone identity
        if settings.SUPERADMIN_PHONE:
            phone_identity = UserIdentity(
                user_id=user.id,
                type=IdentityType.PHONE,
                value=settings.SUPERADMIN_PHONE,
                status=IdentityStatus.VERIFIED,
                is_primary=False,
            )
            db.add(phone_identity)

        await db.commit()
        await db.refresh(user)
        user_id = user.id

    # Assign role (idempotent)
    existing = (await db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id)
    )).scalar_one_or_none()
    if not existing:
        db.add(UserRole(user_id=user_id, role_id=role.id))
        await db.commit()


async def bootstrap_all(db: AsyncSession) -> None:
    # 1) Seed RBAC from JSON
    await seed_rbac_from_json(db)
    # 2) Ensure superadmin account
    await ensure_superadmin(db)
