from functools import wraps
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNotFound
from aiogram.methods import GetChatMember

from kb.user_kb import create_required_tasks_keyboard, create_main_keyboard
from sqlalchemy import func

from config import INITIAL_TASK_REWARD, REQUIRED_CHANNELS

from database.requests import get_session, set_user, user_filters_referrer_id, filtres_user_id

import re

import logging

router = Router()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def extract_channel_username(url: str):
    match = re.search(r"(?:https?:\/\/)?(?:t\.me\/|telegram\.me\/)?(@?)(?P<username>[a-zA-Z0-9_]{5,})/?$", url)
    if match:
        return match.group('username')
    return url

async def check_channel_subscription(user_id: int, channel_username: str) -> InlineKeyboardMarkup:
    try:
        chat_member = GetChatMember(chat_id=f"@{channel_username}", user_id=user_id)
        logger.info(f"User {user_id} subscription status for {channel_username}")
        return chat_member
    except Exception as e:
        if "Bad Request: member list is inaccessible" in str(e):
            logger.error(
                f"Access to member list is restricted for channel {channel_username}. User {user_id} cannot be checked.")
        else:
            logger.error(f"Error checking subscription for user {user_id} in channel {channel_username}: {e}")
        return False
    
async def notify_unsubscribed_users(message: Message):
    session = await get_session()
    user_id = message.from_user.id
    users = await filtres_user_id(user_id=user_id, session=session)

    for user in users:
        user_id = user.tg_id
        is_subscribed = await check_user_subscriptions(user_id=user_id)

        if not is_subscribed:
            try:
                await message.bot.send_message(user_id, "❗Внимание! Вы отписались от следующих каналов: `⚠️ Мы отняли у вас награды за отписку из этих каналов, для возвращения баланса подпишитесь обратно на все каналы, а затем нажмите кнопку ниже:`", reply_markup=await create_required_tasks_keyboard())
                logger.info(f"User {user_id} notified about unsubscription.")
            except TelegramNotFound:
                logger.warning(f"User {user_id} not found or blocked the bot.")    

async def check_user_subscriptions(user_id: int):
    for channel in REQUIRED_CHANNELS:
        channel_username = extract_channel_username(channel['link'])
        if not await check_channel_subscription(user_id, channel_username):
            return False
    return True

def required_tasks_completed(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext = None, *args, **kwargs):
        user_id = message.from_user.id
        user = await filtres_user_id(user_id=user_id)

        if user is None:
            await message.answer("❗️ Пользователь не найден в системе.")
            return

        if not user.initial_task_completed:
            await message.answer("❗️ Для доступа к этой функции необходимо выполнить обязательные задания.",
                                 reply_markup=create_required_tasks_keyboard())
            return

        return await func(message, state, *args, **kwargs)
        session.close()

    return wrapper

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    args = message.text.split()[1:]
    fullname = message.from_user.full_name
    username = message.from_user.username
    session = await get_session()

    user = await filtres_user_id(user_id=user_id, session=session) 

    if not user:
        
        user = await set_user(tg_id=user_id, username=username, fullname=fullname, session=session)  
        if args:
            try:
                referrer_id = int(args[0])
                referrer = await user_filters_referrer_id(referrer_id=referrer_id, session=session)
                if referrer:
                    user.referrer_id = referrer.id  
            except ValueError:
                pass
    else:
        user.fullname = fullname
        
        if not user.initial_task_completed:
            await message.answer(
                "👋 Добро пожаловать! Выполните обязательные задания и получите уже первую награду в 2 UC!:",
                reply_markup=await create_required_tasks_keyboard()
            )
        else:
            await message.answer(
                "👋 Добро пожаловать! Вы уже выполнили обязательные задания. "
                "Вы можете перейти к другим функциям бота.",
                reply_markup=await create_main_keyboard(user_id=user_id)
            )
        
@router.callback_query(F.data.startswith('check_required_tasks'))
async def check_required_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    args = callback.message.text.split()[1:]
    session = await get_session()

    try:
            user = await filtres_user_id(user_id=user_id, session=session)

            if user is None:
                logger.error(f"User with ID {user_id} not found.")
                await callback.answer("Пользователь не найден.", show_alert=True)
                return

            REFERRAL_REWARD = user.balance

            if user.initial_task_completed:
                await callback.answer("❗ Все обязательные задания были выполнены.", show_alert=True)
                await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
                return

            all_subscribed = await check_user_subscriptions(user_id=user_id)
            if all_subscribed:
                user.balance += INITIAL_TASK_REWARD
                user.initial_task_completed = True

                if user.referrer_id:
                    referrer_id = int(args[0])
                    referrer = await user_filters_referrer_id(referrer_id=referrer_id, session=session)
                    if referrer:
                        referrer.balance += REFERRAL_REWARD
                        session.add(referrer)
                        await callback.message.bot.send_message(
                            referrer.tg_id,
                            f"🎉 По вашей реферальной ссылке зашел друг {referrer.full_name}\n\n"
                            f"⭐️Ваш баланс UC: +{user.balance}\n"
                            f"⚡️Теперь вы будете получать 20% с его заработка!\n\n"
                            f"🔗 Продолжай приглашать людей, чтобы быстрее вывести UC!"
                        )

                session.add(user)
                await session.commit()

                try:
                    await callback.answer("✅ Вы успешно прошли все обязательные задания!", show_alert=True)
                    await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
                    await callback.message.bot.send_message(
                        user_id,
                        "📋 Теперь вы можете пользоваться основным функционалом бота.\n\n"
                        "💰 Пригласи друга и получи целых 2 UC в придачу.",
                        reply_markup=await create_main_keyboard(user_id)
                    )
                except TelegramNotFound:
                    logger.warning(f"Invalid query ID for user {user_id}")

            else:
                try:
                    await callback.answer("❌ Вы не подписаны на все каналы.", show_alert=True)
                except TelegramNotFound:
                    logger.warning(f"Invalid query ID for user {user_id}")

    except Exception as e:
        await session.rollback()  
        logger.error(f"Error in check_required_tasks: {e}")