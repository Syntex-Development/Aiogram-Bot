from aiogram.types import Message
from app.database.models import async_session
from app.database.models import User, Admin, SecretCode, Event
from sqlalchemy import select, update, delete




async def tg_ids():#
    async with async_session() as session:
        return await session.scalars(select(User.tg_id).where(User.initial_task_completed==True))

async def set_user(message : Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            referrer_id=int(message.text[7:]) if len(message.text) > 7 else '' 
            tg = message.from_user
            session.add(User(tg_id=tg.id, username=tg.username, full_name=tg.full_name, referrer_id=referrer_id))
            await session.commit()
        return user

async def user(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))
    
    


async def set_balance(tg_id, balance):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(balance=balance))
        await session.commit()

async def balance(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User.balance).where(User.tg_id == tg_id))
      
      
    
    
async def set_admin(tg_id):
    async with async_session() as session:
        session.add(Admin(tg_id=tg_id))
        await session.commit()

async def remove_admin(tg_id):
    async with async_session() as session:
        return await session.execute(delete(Admin).where(Admin.tg_id == tg_id))

async def admins(tg_id):
    async with async_session() as session:
        return await session.scalars(select(Admin.tg_id))




async def set_secret_codes(codes): 
    uniques = []
    not_uniques = []
    
    async with async_session() as session:
        async with session.begin():
            for code in codes:
                try:
                    async with session.begin_nested():
                        session.add(SecretCode(code=code))
                except Exception:
                    not_uniques.append(code)
                else:
                    uniques.append(code)
    
    return uniques, not_uniques
    
async def remove_secret_codes(codes):
    not_remote_codes = []
    
    async with async_session() as session:
        for code in codes:
            result = await session.execute(delete(SecretCode).where(SecretCode.code == code, SecretCode.is_used==False))
            if result.rowcount == 0:
                not_remote_codes.append(code)
        await session.commit()
        
        return not_remote_codes

async def secret_code():
    pass




async def set_event(data):
    async with async_session() as session:
        session.add(Event(**data))
        await session.commit()
        
async def event():
    pass
    
    
    
    
async def set_rank(tg_id, ammount):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(balance=ammount))
        await session.commit()
    