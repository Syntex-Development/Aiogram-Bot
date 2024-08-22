from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)


from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyexpat.errors import messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseChannels
from app.database import requests as rq


from aiogram.enums import ChatMemberStatus
from aiogram.types import Message




from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyexpat.errors import messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseChannels
from app.database.requests import filter_user_id, get_channels






def cancel(data=''):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🚩 Отменить действие', callback_data=f'сancel__{data}')]])

def close(data=''):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔚 Назад', callback_data=f'сlose__{data}')]])



def create_panel():
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='💷 Балансы', callback_data=f'panel__set_balance'),
         InlineKeyboardButton(text='✨ Secret Codes', callback_data=f'panel__set_secret_codes'),],
        [InlineKeyboardButton(text='📤  Отправить сообщение', callback_data=f'panel__set_message'), 
         InlineKeyboardButton(text='📤  Создать розыгрыш', callback_data=f'panel__set_event'),],
        [InlineKeyboardButton(text='🚄 Запустить проверку', callback_data=f'panel__run_check'),     
         InlineKeyboardButton(text='⚙ Изменить задание', callback_data=f'panel__task'),],
        [InlineKeyboardButton(text='🐤 Пользователи', callback_data=f'panel__user'),                
         InlineKeyboardButton(text='👨🏿‍🚀 Администратор', callback_data=f'panel__set_admin'),],
        [InlineKeyboardButton(text='📰 Информация', callback_data=f'panel__info')],
    ]
)

#withdrawal
def uc_count():
    codes_count = rq.get_codes_count()
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=f'`60 UC | {codes_count}`', callback_data='withdrawal_uc')]
    ]
)

def review_kb():
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [InlineKeyboardButton(text="Не хочу оставить отзыв", callback_data="dont_leave_review")]
    ])

def confirm_review_kb():
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_review"),
         InlineKeyboardButton(text="Отменить", callback_data="cancel_review")]
    ])


#menu


def menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='🐵 Профиль'),
                KeyboardButton(text='🔔 Задания')
            ],
            [
                KeyboardButton(text='🏆 ТОП'),
                KeyboardButton(text='💸 Вывод UC')
            ],
            [
                KeyboardButton(text='🎲Мини-игры')
            ],
            [
                KeyboardButton(text='❓ Информация')
            ]
        ]
    )


#mini-games
def games():
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [InlineKeyboardButton(text="Кости", callback_data="dice")]
    ])

#5,30,60

def bet():
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [InlineKeyboardButton(text='5 UC', callback_data='5')],
        [InlineKeyboardButton(text='30 UC', callback_data='30')],
        [InlineKeyboardButton(text='60 UC', callback_data='60')]
    ])



#profile
def back_to_profile_kb():
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='`🔙 Обратно`', callback_data=f'back_to_profile')]
    ]
)


def create_long_confirmation():
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🔊 Отправить', callback_data=f'long_confirmation')],
        [InlineKeyboardButton(text='🔚 Назад', callback_data=f'сlose__')]
    ]
)
   
   
def create_event_task(name, url):
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=name, url = url)],
        [InlineKeyboardButton(text=' ↺ Проверить', callback_data=f'in_chat')]
    ]
)
    
    
async def check_user_subscription_and_generate_keyboard(user_id: int, session: AsyncSession, message: Message) -> InlineKeyboardMarkup | bool:
    result = await session.execute(select(BaseChannels))
    channels = result.scalars().all()
    keyboard = InlineKeyboardBuilder()
    all_subscribed = True
    for channel in channels:
        member = await message.bot.get_chat_member(chat_id=channel.channel_id, user_id=user_id)

        if member.status == ChatMemberStatus.LEFT or member.status == ChatMemberStatus.KICKED:
            all_subscribed = False
            button = InlineKeyboardButton(text=channel.name, url=channel.url)
            keyboard.add(button)
        keyboard.add(InlineKeyboardButton(text='Проверить', callback_data='check_subscription'))
    if all_subscribed:
        return True

    return keyboard.as_markup()

async def main_keyboard(user_id: int, session: AsyncSession) -> ReplyKeyboardMarkup:
    user = await rq.filter_user_id(user_id, session)

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