import asyncio
from datetime import datetime, timezone
from sqlalchemy import text
from app.core.db import AsyncSessionLocal

PURGE_REVOKED_SESSIONS_OLDER_DAYS = 30
PURGE_EXPIRED_OTP_OLDER_DAYS = 7

SQL_EXPIRE_OTP = """
update otp_challenges
set status = 'EXPIRED'
where status in ('CREATED','SENT','FAILED')
  and expires_at <= now();
"""

SQL_EXPIRE_SESSIONS = """
update auth_sessions
set status = 'EXPIRED'
where status = 'ACTIVE'
  and expires_at <= now();
"""

SQL_PURGE_OLD_OTP = """
delete from otp_challenges
where created_at < (now() - (:days || ' days')::interval)
  and status in ('EXPIRED','VERIFIED','LOCKED');
"""

SQL_PURGE_OLD_SESSIONS = """
delete from auth_sessions
where (status in ('REVOKED','EXPIRED'))
  and created_at < (now() - (:days || ' days')::interval);
"""

async def run_cleanup():
    async with AsyncSessionLocal() as db:
        await db.execute(text(SQL_EXPIRE_OTP))
        await db.execute(text(SQL_EXPIRE_SESSIONS))
        await db.execute(text(SQL_PURGE_OLD_OTP), {"days": PURGE_EXPIRED_OTP_OLDER_DAYS})
        await db.execute(text(SQL_PURGE_OLD_SESSIONS), {"days": PURGE_REVOKED_SESSIONS_OLDER_DAYS})
        await db.commit()

if __name__ == "__main__":
    asyncio.run(run_cleanup())

