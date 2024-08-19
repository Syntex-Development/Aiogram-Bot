from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
import asyncio, logging

from app.handlers import router
from app.database.models import create_db, drop_db
from config import config



async def main():
    # await drop_db()
    await create_db()
    bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher()
    dp.include_router(router)
    # await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)
    
    
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass