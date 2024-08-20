import app.database.requests as rq
import app.keyboards as kb

from aiogram.types import Message
from aiogram import Bot
from aiogram.methods import GetChatMember

import logging as logger


        
async def set_message(bot : Bot, from_chat_id, message_id):
    total = 0
    for tg_id in await rq.tg_ids(): 
        try:
            await bot.copy_message(chat_id=tg_id, from_chat_id=from_chat_id, message_id=message_id)
        except:
            pass
        else:
            total+=1
            
        
async def set_event(bot : Bot, data):
    total = 0
    photo = data.photo
    name = data.name
    link = data.link
    chat_id = data.chat_id
    prizes = data.prizes
    time = data.time
    
    reply_markup = kb.create_event_task(name, link)
    if photo:
        await start(dict(photo=photo, caption='Раздача!', reply_markup=reply_markup))
    else:
        await start(dict(text='Раздача!', reply_markup=reply_markup))
    
    async def start(send, data):
        for tg_id in await rq.tg_ids(): 
            try:
                await send(chat_id=tg_id, **data)
            except:
                pass
            else:
                total+=1
            
            
async def in_chat(user, link):
    pass


class Events:
    pass


async def check_channel_sub(user_id: int, channel_username: str):
    try:
        chat_member = GetChatMember(chat_id=f"@{channel_username}", user_id=user_id)
        logger.info(f"User {user_id} subscription status for {channel_username}")
        return True
    except Exception as e:
        if "Bad Request: member list is inaccessible" in str(e):
            logger.error(
            f"Access to member list is restricted for channel {channel_username}. User {user_id} cannot be checked.")
        else:
            logger.error(f"Error checking subscription for user {user_id} in channel {channel_username}: {e}")
        return False