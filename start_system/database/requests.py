from sqlalchemy import select
from .model import async_session, User
from sqlalchemy.ext.asyncio import AsyncSession

async def get_session():
    try:
        session = async_session(autocommit=False, autoflush=False)
        return session
    except Exception as e:
        print(f"Ошибка при создании сессии: {e}")
        return
    finally:
        if session:
            await session.close() 

async def set_user(fullname: str, tg_id: int, username: str, session: AsyncSession):
    new_user = User(username=username, tg_id=tg_id, fullname=fullname)
    session.add(new_user)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e

async def filtres_user_id(user_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == user_id))
    return result.one_or_none()

async def user_filters_referrer_id(referrer_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == referrer_id))
    return result.one_or_none()

