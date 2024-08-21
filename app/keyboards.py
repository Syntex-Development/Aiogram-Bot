from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

import database.requests as rq




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
    
    
