from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import (
    hash_password,
    verify_password,
    generate_api_key_hex,
    encrypt_api_key,
    decrypt_api_key,
    api_key_expiration_from_now
)
from app.crud.user import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    rotate_api_key,
    update_last_login
)
from datetime import datetime, timezone

async def register_user(db: AsyncSession, email: str, username: str, password: str):
    # check uniqueness
    existing = await get_user_by_username(db, username)
    if existing:
        raise ValueError("username_exists")
    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("email_exists")

    pw_hash = hash_password(password)
    
    raw_api_key = generate_api_key_hex()
    enc = encrypt_api_key(raw_api_key)
    expires_at = api_key_expiration_from_now()

    user = await create_user(
        db,
        email=email,
        username=username,
        password_hash=pw_hash,
        api_key_enc=enc,
        api_key_expires_at=expires_at,
    )

async def signin_and_rotate_api_key(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None, None
    # verify password
    if not verify_password(password, user.password_hash):
        return None, None
    
    await update_last_login(db, user.id)
    
    now = datetime.now(timezone.utc)
    if user.api_key_enc and user.api_key_expires_at and user.api_key_expires_at > now:
        try:
            raw_api_key = decrypt_api_key(user.api_key_enc)
        except ValueError:
            # decryption failed — treat like expired/missing and rotate
            raw_api_key = None

        if raw_api_key:
            return user, raw_api_key

    # either no key, decryption failed, or expired => generate new
    raw_api_key = generate_api_key_hex()
    enc = encrypt_api_key(raw_api_key)
    expires_at = api_key_expiration_from_now()
    updated_user = await rotate_api_key(db, user.id, enc, expires_at)
    return updated_user, raw_api_key
