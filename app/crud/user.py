from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from app.models.user import User
from typing import Optional

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = select(User).where(User.username == username)
    res = await db.execute(q)
    return res.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email.ilike(email))
    res = await db.execute(q)
    return res.scalars().first()

async def get_user_by_api_key_hash(db: AsyncSession, api_key_hash: bytes) -> Optional[User]:
    q = select(User).where(User.api_key_hash == api_key_hash, User.api_key_revoked == False)
    res = await db.execute(q)
    return res.scalars().first()

async def create_user(db: AsyncSession, *, email: str, username: str, password_hash: str, api_key_enc: bytes, api_key_expires_at):
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        api_key_enc=api_key_enc,
        api_key_expires_at=api_key_expires_at,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise

async def rotate_api_key(db: AsyncSession, user_id, new_api_key_hash: bytes, expires_at):
    q = (
        update(User)
        .where(User.id == user_id)
        .values(
            api_key_hash=new_api_key_hash,
            api_key_created_at=datetime.now(timezone.utc),
            api_key_expires_at=expires_at,
            api_key_revoked=False
        )
        .returning(User)
    )
    res = await db.execute(q)
    await db.commit()
    return res.scalars().first()

async def revoke_api_key(db: AsyncSession, user_id):
    q = update(User).where(User.id == user_id).values(api_key_revoked=True)
    await db.execute(q)
    await db.commit()

async def update_last_login(db: AsyncSession, user_id):
    q = update(User).where(User.id == user_id).values(last_login_at=datetime.now(timezone.utc))
    await db.execute(q)
    await db.commit()
