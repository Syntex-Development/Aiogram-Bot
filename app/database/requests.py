from aiogram.types import Message
from app.database.models import async_session
from app.database.models import User, Admin, SecretCode, Event, TaskCompletion, Task, Withdrawal, Achievements, BaseChannels
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload, joinedload, aliased, selectinload

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

async def user(tg_id, session: AsyncSession):
    return await session.scalar(select(User).where(User.tg_id == tg_id))    
    
async def get_user(tg_id: int, session: AsyncSession):
    async with async_session() as session:
        user = await session.execute(select(User).filter_by(tg_id=tg_id))
        return user.scalar_one_or_none()


async def set_balance(tg_id, balance, ):
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(balance=balance))
        await session.commit()

async def add_balance(tg_id, amount, session: AsyncSession):
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

async def add_user(tg_id: int, session: AsyncSession):
    existing_user = await session.one_or_none(select(User).filter(User.tg_id == tg_id))
    if existing_user:
        return existing_user

    new_user = User(tg_id=tg_id)
    session.add(new_user)
    await session.commit()
    return new_user



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
    result = await session.execute(
        select(func.count(User.tg_id)).where(User.referrer_id == tg_id)
    )
    return result.scalar()

#Tasks
async def get_tasks(tg_id, message, session: AsyncSession):
    user_result = await session.execute(select(User).filter(User.tg_id == tg_id))
    user = user_result.scalars().first()

    tasks_result = await session.execute(select(Task).filter(Task.is_active == True))
    tasks = tasks_result.scalars().all()

    available_tasks = []
    for task in tasks:
        completion_result = await session.execute(select(TaskCompletion).filter(
            TaskCompletion.user_id == user.id,
            TaskCompletion.task_id == task.id
        ))
        completion = completion_result.scalars().first()

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
async def get_top_users(limit: int, session: AsyncSession):
    Referral = aliased(User)

    result = await session.execute(
        select(User)
        .outerjoin(Referral, Referral.referrer_id == User.id)
        .group_by(User.id)
        .order_by(func.count(Referral.id).desc())
        .limit(limit)
    )

    top_users = result.scalars().all()
    return top_users

async def get_user_top_position(user_id: int, session: AsyncSession):
    user_alias = aliased(User)

    result = await session.execute(
        select(User).filter(User.tg_id == user_id)
    )
    user = result.scalars().first()

    if user and user.is_hidden:
        return None

    subquery = (
        select(user_alias.id, func.count().label("referrals_count"))
        .join(user_alias.referrals)
        .group_by(user_alias.id)
        .subquery()
    )

    result = await session.execute(
        select(User, subquery.c.referrals_count)
        .outerjoin(subquery, User.id == subquery.c.id)
        .order_by(subquery.c.referrals_count.desc())
    )
    
    top_users = result.all()

    position = 0
    for i, (user_in_top, _) in enumerate(top_users):
        if user_in_top.tg_id == user_id:
            position = i + 1
            break
            
    return position

async def hide_user_in_top(user_id: int, session: AsyncSession):
    stmt = select(User).where(User.tg_id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user:
        user.is_hidden_in_top = True
        await session.commit()

async def show_user_in_top(user_id: int, session: AsyncSession):
    user_ = await user(user_id)
    user_.is_hidden_in_top = False
    await session.commit()


#Withdrawal
async def get_stat_withdrawal(session: AsyncSession):
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
async def find_opponent(tg_id: int, bet_amount: int, session: AsyncSession):
    opponent_query = select(User).where(
        User.tg_id != tg_id,
        User.balance >= bet_amount,
        User.wait_dice_game == True
    ).order_by(User.id).limit(1)

    opponent = await session.execute(opponent_query)
    result = opponent.scalar_one_or_none()

    if result:
        result.wait_dice_game = False
        await session.commit()

    return result
    
async def update_user_waiting_status(tg_id: int, waiting: bool, session: AsyncSession):
    user = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = user.scalar_one_or_none()

    if user:
        user.wait_dice_game = waiting
        await session.commit()
        
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


async def get_achievements_count(tg_id, session: AsyncSession):
    result = await session.execute(
        select(User).options(selectinload(User.achievements)).filter(User.tg_id == tg_id)
    )
    user = result.scalars().first()

    if user:
        taked_achievements_count = len(user.achievements)
        return taked_achievements_count

    return 0