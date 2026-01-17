from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import anyio
import secrets, hashlib

_ph = PasswordHasher()

async def hash_password_async(password: str) -> str:
    return await anyio.to_thread.run_sync(_ph.hash, password)

async def verify_password_async(password: str, password_hash: str) -> bool:
    def _verify():
        try:
            return _ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False
    return await anyio.to_thread.run_sync(_verify)

async def needs_rehash_async(password_hash: str) -> bool:
    return await anyio.to_thread.run_sync(_ph.check_needs_rehash, password_hash)

def random_token_urlsafe(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
