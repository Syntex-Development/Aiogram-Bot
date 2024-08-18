from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



close           = [InlineKeyboardButton(text='✖ Закрыть', callback_data='!сlose')]
cancel          = [InlineKeyboardButton(text='✖ Отмена', callback_data='!сancel')]
bottom_close    = InlineKeyboardMarkup(inline_keyboard=[close])
bottom_cancel   = InlineKeyboardMarkup(inline_keyboard=[cancel])
bottom          = InlineKeyboardMarkup(inline_keyboard=[close, cancel])
    
    
def create_panel():
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отправить сообщение | Создать розыгрыш', callback_data=f'panel__enter_message')],
        [InlineKeyboardButton(text='Просмотреть профиль пользователя', callback_data=f'panel__check_user')],
        [InlineKeyboardButton(text='Новое задание | Изменить задание', callback_data=f'panel__new_task')],
        [InlineKeyboardButton(text='Изменить баланс пользователя', callback_data=f'panel__update_balance')],
        [InlineKeyboardButton(text='Добавить коды активации', callback_data=f'panel__add_secret_codes')],
        [InlineKeyboardButton(text='Запустить проверку', callback_data=f'panel__run_check')],
        [InlineKeyboardButton(text='Добавить админа', callback_data=f'panel__add_admin')],
        [InlineKeyboardButton(text='Информация', callback_data=f'panel__info')],
    ]
)

