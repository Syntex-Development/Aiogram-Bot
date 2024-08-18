from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from textwrap import dedent as dd



from middlewares import TestMiddleware1, TestMiddleware2
from config import config
from . import filters
from . import states
import app.resources.tools as tools
import app.database.requests as rq 
import app.keyboards as kb


router = Router()
router.callback_query.outer_middleware(TestMiddleware1())
router.message.outer_middleware(TestMiddleware2())


@router.message(CommandStart())
async def handler(message: Message):
    # await rq.set_user(message)
    await message.answer(dd(
        '''📋 Теперь вы можете пользоваться основным функционалом бота.
        💰 Пригласи друга и получи целых 2 UC в придачу.
        '''
    ))
