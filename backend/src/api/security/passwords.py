import asyncio
import gzip
import secrets
from functools import cache
from pathlib import Path

from argon2 import PasswordHasher

hasher = PasswordHasher()

DUMMY_PASSWORD_HASH: str = hasher.hash(secrets.token_urlsafe(32))
PASSWORD_BLACKLIST_PATH: Path = (
    Path(__file__).resolve().parent / "password_blacklist.txt.gz"
)
PASSWORD_BLACKLIST_URL: str = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/Pwdb_top-1000000.txt"


@cache
def password_blacklist() -> frozenset[str]:
    with gzip.open(PASSWORD_BLACKLIST_PATH, mode="rt", encoding="utf-8") as file:
        return frozenset(line.rstrip("\n") for line in file)


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(hasher.hash, password)
