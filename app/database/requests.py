from app.database.models import async_session
from app.database.models import User, Admin
from aiogram.types import Message
from sqlalchemy import select, update


async def set_user(message : Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            referrer_id=int(message.text[7:]) if len(message.text) > 7 else '' 
            tg = message.from_user
            session.add(User(tg_id=tg.id, username=tg.username, full_name=tg.full_name, referrer_id=referrer_id))
            await session.commit()
        return user
        

async def tg_ids():
    async with async_session() as session:
        return await session.scalars(select(User.tg_id))
    
    
async def set_rank(tg_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(rank_id=User.rank_id + 1))
        await session.commit()


async def admins():
    async with async_session() as session:
        return await session.scalars(select(Admin.tg_id))