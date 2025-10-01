import secrets
from cryptography.fernet import InvalidToken, Fernet
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.core.db_config import db_settings

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
FERNET = Fernet(db_settings.FERNET_KEY)

# Password helpers
def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

# API Key helpers
def generate_api_key_hex(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)

def encrypt_api_key(raw: str) -> str:
    return FERNET.encrypt(raw.encode("utf-8")).decode("utf-8")

def decrypt_api_key(enc: str) -> str:
    try:
        return FERNET.decrypt(enc.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("invalid encrypted token or bad key")

def api_key_expiration_from_now(days: int | None = None, start: datetime | None = None) -> datetime:
    if days is None:
        days = db_settings.API_KEY_EXPIRE_DAYS
    if start is None:
        start = datetime.now(timezone.utc)
    return start + timedelta(days=days)
