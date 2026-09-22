import asyncio
import gzip
import secrets
from functools import cache
from pathlib import Path

from argon2 import PasswordHasher
from pydantic import SecretStr

hasher = PasswordHasher()

BLACKLIST_PATH: Path = Path(__file__).resolve().parent / "password_blacklist.txt.gz"
BLACKLIST_URL: str = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/Pwdb_top-1000000.txt"
DUMMY_HASH: str = hasher.hash(secrets.token_urlsafe(32))


@cache
def blacklist() -> frozenset[str]:
    with gzip.open(BLACKLIST_PATH, mode="rt", encoding="utf-8") as file:
        return frozenset(line.rstrip("\n") for line in file)


def ensure_not_blacklisted(password: SecretStr) -> SecretStr:
    value: str = password.get_secret_value()
    if value.lower() in blacklist():
        raise ValueError("Password is too common, choose a less predictable one")
    return password


async def hash(password: str) -> str:
    return await asyncio.to_thread(hasher.hash, password)
