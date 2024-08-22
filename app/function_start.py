from functools import wraps
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNotFound
from aiogram.methods import GetChatMember
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import create_required_tasks_keyboard, main_keyboard
from sqlalchemy import func

from config import settings

from app.database.requests import set_user, user_filters_referrer_id, filter_user_id, get_channels

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
    
async def notify_unsubscribed_users(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    users = await filter_user_id(user_id=user_id, session=session)

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
    channels = await get_channels()
    for channel in channels:
        channel_username = extract_channel_username(channel.link)
        if not await check_channel_subscription(user_id, channel_username):
            return False
    return True

def required_tasks_completed(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext = None, *args, **kwargs):
        user_id = message.from_user.id
        user = await filter_user_id(user_id=user_id)

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