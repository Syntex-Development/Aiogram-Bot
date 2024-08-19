from aiogram.fsm.state import StatesGroup, State


class SecretCodes(StatesGroup):
    codes = State()

class Admin(StatesGroup):
    tg_id = State()

class Message(StatesGroup):
    message = State()

class Event(StatesGroup):
    photo = State()
    name = State()
    link = State()
    chat_id = State()
    prizes = State()
    time = State()
    
class Balance(StatesGroup):
    tg_id = State()
    amount = State() 