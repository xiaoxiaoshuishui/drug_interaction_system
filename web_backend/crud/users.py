import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security
from utils.security import verify_password


async def get_user(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserRequest):
    hashed_pwd = security.get_hashed_password(user_data.password)
    new_user = User(
        username=user_data.username,
        password=hashed_pwd
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def create_token(db: AsyncSession, user_id: int):
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=1)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(user_token)
        await db.commit()

    return token

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()
    expires_at = user_token.expires_at
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if not user_token or expires_at < datetime.now():
        return None
    query = select(User).where(User.id == user_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_user_info(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    query = update(User).where(User.username == username).values(**user_data.model_dump(exclude_unset=True,exclude_none=True))
    res = await db.execute(query)
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    updated_user = await get_user(db, username)
    return updated_user

async def change_user_password(db: AsyncSession, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.password):
        raise False
    hashed_pwd = security.get_hashed_password(new_password)
    user.password = hashed_pwd
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True