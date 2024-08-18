from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    add_task_category = State()
    add_task_link = State()
    add_task_reward = State()
    add_task_completions = State()
    add_secret_codes = State()

class UserInput(StatesGroup):
    id = State()




class Form(StatesGroup):
    message = State()
    admin = State()
    user = State()
    balance = State()
    secret_codes = State()