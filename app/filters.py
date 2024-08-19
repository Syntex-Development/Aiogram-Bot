from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.database import requests as rq
from datetime import datetime, timedelta
from dateutil import parser
from app.database import requests as rq



class IsDateTimeFormat(BaseFilter):
    '''
    Minimum Event Time      -> 3 Hours
    correct format          -> XXXX-XX-XX xx:xx:xx
    
    input 11-11             -> XXXX-XX-XX 08:25:xx
    input 08:25             -> XXXX-XX-XX 08:25:xx
    input 30 13:30          -> XXXX-XX-30 13:30:xx
    input 12-04 23:59       -> XXXX-12-04 23:59:xx
    input 2025-01-01 00:01  -> 2025-01-01 00:01:xx

    '''
    
    async def __call__(self, message: Message) -> bool:
        minimum_event_time = timedelta(hours=3)
        
        if not message.text.split(':'):
            return False
        now = datetime.now()
        try:
            dt = parser.parse(message.text, fuzzy=False)
            dt = dt.replace(year=dt.year or now.year, month=dt.month or now.month, day=dt.day or now.day, second=1, microsecond=1)
            if dt > now + minimum_event_time:
                return dict(dt=dt)
        except ValueError:
            return False


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in await rq.admins()
    
    
class IsPrizesFormat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return len(message.text.split()) <=5


class IsDBUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text.isdigit and len(message.text) > 7:
            return dict(user = await rq.user(int(message.text)))