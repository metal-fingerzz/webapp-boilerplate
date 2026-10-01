import hashlib
import secrets

TOKEN_BYTE_COUNT: int = 32


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTE_COUNT)
