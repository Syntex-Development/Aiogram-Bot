import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

from app.handlers import router
from app.database.models import create_db, async_session
from app.middlewares import DataBaseSession, LoggingMiddleware

from config import settings


bot = Bot(token=settings.token, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()


async def main():
    await create_db()

    dp.include_router(router)
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    dp.update.middleware(LoggingMiddleware())

    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass