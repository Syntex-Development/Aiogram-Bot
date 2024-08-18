from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.database import requests as rq


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in await rq.admins()