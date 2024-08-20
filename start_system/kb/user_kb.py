from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from database.requests import filtres_user_id, get_session
from .config import REQUIRED_CHANNELS

async def create_required_tasks_keyboard():
    channel_buttons = [[InlineKeyboardButton(text=channel['name'], url=channel['link'])] for channel in
                       REQUIRED_CHANNELS]
    check_button = [InlineKeyboardButton(text="✅ Проверить", callback_data="check_required_tasks")]

    buttons = channel_buttons + [check_button]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard

async def create_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    session = await get_session()
    user = await filtres_user_id(user_id=user_id, session=session)

    if user and user.initial_task_completed:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Задания"), KeyboardButton(text="👨 Профиль")],
                [KeyboardButton(text="💸 Вывести"), KeyboardButton(text="🏆 ТОП")],
                [KeyboardButton(text="❓ Ответы на вопросы")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Выполнить обязательные задания")],
                [KeyboardButton(text="❓ Ответы на вопросы")]
            ],
            resize_keyboard=True
        )

    return keyboard