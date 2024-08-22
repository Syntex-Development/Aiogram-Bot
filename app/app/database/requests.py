from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Admin, SecretCode, Event, TaskCompletion, Task, BaseChannels
from sqlalchemy import select, update, delete

async def update_user(session: AsyncSession, user_id: int, **kwargs):
    if not kwargs:
        return False

    stmt = update(User).where(User.tg_id == user_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

async def filter_user_id(user_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == user_id))
    return result.one_or_none()
async def user_filters_referrer_id(referrer_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == referrer_id))
    return result.one_or_none()

async def tg_ids(session: AsyncSession):#
    return await session.scalars(select(User.tg_id).where(User.initial_task_completed==True))

async def set_user(message: Message, session: AsyncSession):
    user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
    args = message.text.split()[1:]
    referrer_id = 0

    if not user:
        if len(args) > 0:
            try:
                referrer_id = int(args[0])
            except ValueError:
                referrer_id = 0
        tg = message.from_user
        session.add(User(
            tg_id=tg.id,
            username=tg.username,
            full_name=tg.full_name,
            referrer_id=referrer_id
        ))
        await session.commit()

    return user

async def user(tg_id, session: AsyncSession):
    return await session.scalar(select(User).where(User.tg_id == tg_id))


async def set_balance(tg_id, balance, session: AsyncSession):
        await session.execute(update(User).where(User.tg_id == tg_id).values(balance=balance))
        await session.commit()

async def add_balance(tg_id, amount, session: AsyncSession):
        user_result = await session.scalars(select(User).filter(User.tg_id == tg_id))
        user = user_result.first()
        user.balance += amount
        await session.commit()

async def balance(tg_id, session: AsyncSession):
        return await session.scalar(select(User.balance).where(User.tg_id == tg_id))

    
async def set_admin(tg_id, session: AsyncSession):
    session.add(Admin(tg_id=tg_id))
    await session.commit()

async def remove_admin(tg_id, session: AsyncSession):
    return await session.execute(delete(Admin).where(Admin.tg_id == tg_id))

async def admins(tg_id, session: AsyncSession):
    return await session.scalars(select(Admin.tg_id))




async def set_secret_codes(codes, session: AsyncSession):
    uniques = []
    not_uniques = []

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
    
async def remove_secret_codes(codes, session: AsyncSession):
    not_remote_codes = []

    for code in codes:
        result = await session.execute(delete(SecretCode).where(SecretCode.code == code, SecretCode.is_used==False))
        if result.rowcount == 0:
            not_remote_codes.append(code)
    await session.commit()

    return not_remote_codes

async def secret_code():
    pass




async def set_event(data, session: AsyncSession):
    session.add(Event(**data))
    await session.commit()
        
async def event():
    pass
    
    
    
    
async def set_rank(tg_id, ammount, session: AsyncSession):
    await session.execute(update(User).where(User.tg_id == tg_id).values(balance=ammount))
    await session.commit()

#Tasks
async def get_tasks(tg_id, message, session: AsyncSession):

    user_result = await session.scalars(select(User).filter(User.tg_id == tg_id))
    user = user_result.first()

    user_result = await session.scalars(select(Task).filter(Task.is_active == True))
    tasks = user_result.all()

    available_tasks = []
    for task in tasks:
        completion = session.query(TaskCompletion).filter(
            TaskCompletion.user_id == user.id,
            TaskCompletion.task_id == task.id
        ).first()

        if not completion:
            available_tasks.append(task)

    if not available_tasks:
        return False
    return available_tasks


async def get_task_by_id(task_id, session: AsyncSession):
    user_result = await session.scalars(select(Task).filter(Task.id == task_id))
    task = user_result.first()
    return task
    

#Top users
async def get_top_users(limit: int, session: AsyncSession):
    top_users_result = await session.scalar(select(User).order_by(User.refferals_count.desc()))
    top_users = top_users_result.all()
    return top_users

async def get_user_top_position(user_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == user_id))
    result_user = result.first()
    if result_user and result_user.is_hidden_in_top:
        return None
    top_users_result = await session.scalar(select(User).order_by(User.refferals_count.desc()))
    top_users = top_users_result.all()
    position = 0
    for i, user_in_top in enumerate(top_users):
        if user_in_top.tg_id == user_id:
            position = i + 1
            break
    return position

async def hide_user_in_top(user_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == user_id))
    result_user = result.first()
    result_user.is_hidden_in_top = True
    await session.commit()

async def show_user_in_top(user_id: int, session: AsyncSession):
    result = await session.scalars(select(User).filter(User.tg_id == user_id))
    result_user = result.first()
    result_user.is_hidden_in_top = False
    await session.commit()

async def get_channels(channels_id: int, session: AsyncSession):
    result = await session.scalars(select(BaseChannels).filter(BaseChannels.channel_id == channels_id))
    return result