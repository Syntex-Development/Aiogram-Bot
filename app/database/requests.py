from aiogram.types import Message
from app.database.models import async_session
from app.database.models import User, Admin, SecretCode, Event, TaskCompletion, Task, Withdrawal, Achievements, BaseChannels
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession





async def tg_ids():#
    async with async_session() as session:
        return await session.scalars(select(User.tg_id).where(User.initial_task_completed==True))

async def set_user(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            referrer_id = int(message.text[7:]) if len(message.text) > 7 and message.text[7:].isdigit() else None
            tg = message.from_user
            username = tg.username if tg.username else ""
            new_user = User(tg_id=tg.id, username=username, full_name=tg.full_name)
            if referrer_id:
                new_user.referrer_id = referrer_id
            session.add(new_user)
            await session.commit()
        return user

async def user(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))    
    
async def get_user(tg_id: int, session: AsyncSession):
    async with async_session() as session:
        user = await session.execute(select(User).filter_by(tg_id=tg_id))
        return user.scalar_one_or_none()


async def set_balance(tg_id, balance):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(balance=balance))
        await session.commit()

async def add_balance(tg_id, amount):
    async with async_session() as session:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        user.balance += amount
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


#Profile
        
async def get_referral_count_by_tg_id(tg_id: int, session: AsyncSession):
    async with async_session() as session:
        result = await session.execute(
            select(func.count(User.tg_id)).where(User.referrer_id == tg_id)
        )
        return result.scalar()

#Tasks
async def get_tasks(tg_id, message):
    async with async_session() as session:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        tasks = session.query(Task).filter(Task.is_active == True).all()

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


async def get_task_by_id(task_id):
    async with async_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        return task
    

#Top users
async def get_top_users(limit: int):
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .outerjoin(User.referrals)  # Объединяем с таблицей рефералов
            .group_by(User.id)  # Группируем по пользователям
            .order_by(func.count(User.referrals).desc())  # Считаем количество рефералов и сортируем
            .limit(limit)
        )
        top_users = result.scalars().all()  # Получаем только пользователей
        return top_users

async def get_user_top_position(user_id: int):
    async with async_session() as session:
        user = session.query(User).filter(User.tg_id == user_id).first()
        if user and user.is_hidden_in_top:
            return None
        top_users = session.query(User).order_by(User.refferals_count.desc()).all()
        position = 0
        for i, user_in_top in enumerate(top_users):
            if user_in_top.tg_id == user_id:
                position = i + 1
                break
        return position

async def hide_user_in_top(user_id: int):
    async with async_session() as session:
        user = session.query(User).filter(User.tg_id == user_id).first()
        user.is_hidden_in_top = True
        await session.commit()

async def show_user_in_top(user_id: int):
    async with async_session() as session:
        user = session.query(User).filter(User.tg_id == user_id).first()
        user.is_hidden_in_top = False
        await session.commit()


#Withdrawal
async def get_stat_withdrawal(session: AsyncSession):
    async with async_session() as session:
        stat = await session.execute(select(Withdrawal))
        return stat.scalar_one_or_none()
        

async def get_codes_count():
    async with async_session() as session:
        #сделать получение кол-ва доступных кодов
        pass


async def get_activation_code():
    async with async_session() as session:
        code = session.query(SecretCode).filter(SecretCode.is_used == False).first()
        if code:
            code.is_used = True
            await session.commit()
            return code.code
        else:
            return None


async def update_withdrawal_stat():
    async with async_session() as session:
        withdrawal_stat = session.query(Withdrawal).first()
        if withdrawal_stat:
            withdrawal_stat.bot_withdrawal_count += 1
            withdrawal_stat.bot_withdrawal_sum += 60
        else:
            session.add(Withdrawal())
        await session.commit()


#Mini-games
async def find_opponent(tg_id: int, bet_amount: int):
    async with async_session() as session:
        opponent = await session.execute(
            select(User).where(
                User.tg_id != tg_id, 
                User.balance >= bet_amount, 
                User.in_dice_game == False
            )
        )
        
#Achievements
async def add_achievement(tg_id: int, achievement_name: str):
    async with async_session() as session:
        user = await session.execute(
            select(User).options(selectinload(User.achievements)).where(User.tg_id == tg_id)
        )
        user = user.scalar_one_or_none()

        if user:
            existing_achievement = next(
                (
                    achievement
                    for achievement in user.achievements
                    if achievement.name == achievement_name
                ),
                None,
            )
            if not existing_achievement:
                new_achievement = Achievements(user=user, name=achievement_name)
                session.add(new_achievement)
                await session.commit()
                return True
            else:
                return False
        else:
            return False
        
#config
async def get_channels(channels_id: int, session: AsyncSession):
    result = await session.scalars(select(BaseChannels).filter(BaseChannels.channel_id == channels_id))
    return result.all()


async def set_access(tg_id, session: AsyncSession):
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user.scalar_one_or_none()

        if user:
            await session.execute(
                update(User)
                .where(User.tg_id == tg_id)
                .values(initial_task_completed=True)
            )
            await session.commit()