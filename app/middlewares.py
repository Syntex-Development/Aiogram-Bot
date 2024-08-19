from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from unittest.mock import sentinel
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject


class TestMiddleware1(BaseMiddleware):
    async def __call__(self, handler: Callable [[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict [str, Any]):
        result = await handler(event, data)
        await event.answer()
        print(event.data)
        return result

class TestMiddleware2(BaseMiddleware):
    async def __call__(self, handler: Callable [[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict [str, Any]):
        result = await handler(event, data)
        if result == sentinel.UNHANDLED:
            await event.delete()
        return result
