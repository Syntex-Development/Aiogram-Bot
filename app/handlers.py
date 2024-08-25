from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNotFound, DetailedAiogramError, TelegramAPIError
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy.ext.asyncio import AsyncSession

from textwrap import dedent as dd
from types import SimpleNamespace as asdataclass

from app.middlewares import TestMiddleware1, TestMiddleware2
from app.database import requests as rq

from . import filters
from . import states

from random import randint

from logging import Logger

from dotenv import load_dotenv

import app.resources.tools as tools
import app.keyboards as kb
import asyncio
import os
import time

router = Router()
router.callback_query.outer_middleware(TestMiddleware1())
router.message.outer_middleware(TestMiddleware2())

load_dotenv()
bot = Bot(token=os.getenv('TOKEN'))

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, logger: Logger):
    user_id = message.from_user.id
    try:
        referrer_id = None
        if len(message.text.split()) > 1:
            referrer_id = message.text.split()[1]
            if referrer_id.isdigit():
                referrer_id = int(referrer_id)
            else:
                await message.answer("Неверный ID реферала. Попробуйте снова.")
                return 

        user = await rq.get_user(tg_id=user_id, session=session)
        if user == None:
            await rq.set_user(message)

        if referrer_id:
            referrer = await rq.get_user(tg_id=referrer_id, session=session)  
            if referrer:
                await rq.update_user(session, user_id, referrer_id=referrer_id) 

        if user:
            if not user.initial_task_completed:
                await message.answer(
                    text="👋 Добро пожаловать! Выполните обязательные задания и получите уже первую награду в 2 UC!",
                    reply_markup=await kb.create_required_tasks_keyboard(session)
                )
            else:
                await message.answer(
                    text=("👋 Добро пожаловать! Вы уже выполнили обязательные задания. "
                          "Вы можете перейти к другим функциям бота."),
                    reply_markup=await kb.main_keyboard(message.from_user.id, session)
                )

    except Exception as e:
        logger.error(f"Error command /start: {e}")
    except TelegramNotFound:
        logger.error(f"User {user_id} not found, unable to send /start message.")


@router.message(F.text == '🔔 Задания')
async def tasks_handler(message: Message, session: AsyncSession):
    tg_id = message.from_user.id
    tasks = await rq.get_tasks(tg_id, message, session)

    if tasks is False:
        await message.answer('❌ В данный момент для вас нет доступных заданий.', reply_markup= kb.back_to_profile_kb())
    elif tasks:
        keyboard = InlineKeyboardBuilder()
        for task in tasks:
            keyboard.add(
                InlineKeyboardButton(
                    text=task.name, 
                    callback_data=f"task_{task.id}" 
                )
            )

        await message.answer(
            "📋 Вот список доступных заданий для вас:", 
            reply_markup=keyboard.as_markup()
        )


# Callback check_subscription (кнопки проверить подписку)
@router.callback_query(F.data == 'check_required_tasks')
async def check_subs_chnls(callback: CallbackQuery, session: AsyncSession):
    user = await rq.user(callback.from_user.id, session=session)
    channels = await rq.get_channels(channels_id=-1002228388262, session=session)
    channel_ids = [channel.channel_id for channel in channels]

    is_subscribed = True

    for channel in channel_ids:
        status = await tools.check_channel_sub(callback.from_user.id, channel)
        if not status:
            is_subscribed = False
            break 

    if is_subscribed:
        await callback.message.edit_text("✅ Вы подписаны на все каналы!",show_alert=True)
        await rq.set_access(callback.from_user.id, session)
        
        await callback.message.answer('Добро пожаловать в бота!', reply_markup=await kb.main_keyboard(callback.from_user.id, session))
    else:
        await callback.message.edit_text("❌ Вы не подписаны на один или несколько каналов.", show_alert=True)

@router.callback_query(F.data == 'сlose__')
async def panel(callback : CallbackQuery, state: FSMContext):
    if not await state.get_data():
        await callback.message.edit_text('🏬 Admin  panel.   Control  Center.', reply_markup=kb.create_panel())
    else:
        await callback.message.edit_reply_markup()
        await callback.message.answer('/panel')
        await callback.message.answer('🏬 Admin  panel.   Control  Center.', reply_markup=kb.create_panel())
    await state.clear()
    
@router.message(Command('panel'), filters.IsAdmin())
async def panel_as_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('🏬 Admin  panel.  Control  Center.', reply_markup=kb.create_panel())

 
 
# админы
@router.callback_query(F.data == 'panel__set_admin')
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text('⌨️  Set  Administrator.   Please,  start  enter ...', reply_markup=kb.close())
    await state.set_state(states.Admin.tg_id)
    
@router.message(states.Admin.tg_id, filters.IsDBUser())
async def handler(message: Message, state : FSMContext, user):
    tg_id = int(message.text) 
    if tg_id in await rq.admins(tg_id):
        await message.answer(f'❕❗️ [ {tg_id} ]  Is  Administrator !', reply_markup=kb.close())
    else: 
        await message.answer(f'⭐️ New  administrator  [ {tg_id} ]', reply_markup=kb.cancel(f"admin:{tg_id}"))
        await rq.set_admin(tg_id)
        await state.set_state()
        
@router.callback_query(F.data.startswith('сancel__admin'))
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f'<s>{callback.message.text}</s>')
    data = callback.data.split(":")[1:]
    await rq.remove_admin(*data)
        
        
        
# коды
@router.callback_query(F.data == 'panel__set_secret_codes')
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text('⌨️ New  Secret  Code.   Please,  start  enter ...', reply_markup=kb.close())
    await state.set_state(states.SecretCodes.codes)

@router.message(states.SecretCodes.codes, F.text)
async def handler(message: Message, state : FSMContext):
    uniques, not_uniques = await rq.set_secret_codes(message.text.split('\n'))
    
    await message.answer(
        text=(
            "🗳 New   Secret   Codes\n"
            "\n"
            "{}\n"
            "\n"
            "All  Unique : [ {} ]\n"
            "\n"
            "<s>{}</s>"
        ).format(
            "\n".join(uniques) if uniques else '',
            len(uniques),
            "\n".join(not_uniques)
        ),
        reply_markup=kb.cancel('secret_codes'))

@router.callback_query(F.data == 'сancel__secret_codes')
async def handler(callback : CallbackQuery, state: FSMContext):
    data = callback.message.text.split("\n\n")
    code_unigues = data[1]
    
    if code_unigues:
        not_remote_codes = await rq.remove_secret_codes(code_unigues.split('\n'))
        
        last_text   = "\n".join(data)
        last_text   = f"<s>{last_text}</s>"
        result_text = "\n".join(f'❗️{item}' for item in not_remote_codes)
        result_text = result_text if not_remote_codes else ""
        full_text   = f"{last_text}\n\n❗️ <b>Эти коды уже использовали:</b>  ❗️\n\n{result_text}"
        
        await callback.message.edit_text(full_text)



# сообщения
@router.callback_query(F.data == 'panel__set_message')
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text('📤 Send  a  Message  to  everyonee.  Please,  start  enter ...', reply_markup=kb.close())
    await state.set_state(states.Message.message)
     
@router.message(states.Message.message)
async def handler(message: Message, state : FSMContext):
    await message.answer('💬 The   bot   caught   the   message', reply_markup=kb.create_long_confirmation())
    await state.update_data(message_id = message.message_id, confirmation_value=2)
    
@router.callback_query(states.Message.message, F.data=='long_confirmation')
async def handler(callback : CallbackQuery, state: FSMContext):
    data = asdataclass(**(await state.get_data()))
    await callback.answer(f'{data.confirmation_value}')
    await state.update_data(confirmation_value = data.confirmation_value-1)
    if data.confirmation_value == 0:
        mess = callback.message
        total = await tools.set_message(bot = mess.bot, from_chat_id = mess.chat.id, message_id = data.message_id)
        await callback.message.edit_text(f'❕❕  [ {total} ]  users  got  a  message!', reply_markup=kb.cancel())
        await state.set_state()
    


# раздачи
@router.callback_query(F.data == 'panel__set_event')
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text(dd(
        '''
        📤 Send  a  Event  to  everyone.   Start  writing:
        
        * Photo
        Name
        Channel  Link
        ** Channel  ID
        Prizes  1-5
        Time
        
        *  Use  `0`  to  skip 
        **  Use  `0`  to  skip  <b>IF POSSIBLE</b>
        

        Please  Enter  Photo ...  
        '''), reply_markup=kb.close())
    await state.set_state(states.Event.photo)
    
@router.message(states.Event.photo, F.photo)
@router.message(states.Event.photo, F.text=='0')
async def handler(message: Message, state : FSMContext):
    photo = message.photo[-1] if message.photo else None
    await state.update_data(photo= photo)
    await message.answer('Photo :    {}  !\nStart   enter   Name ...'.format('Done' if photo else 'Skipped'))
    await state.set_state(states.Event.name)
    
@router.message(states.Event.name, F.text)
async def handler(message: Message, state : FSMContext):
    await state.update_data(name= message.text)
    await message.answer('Name :    Done  !\nStart   enter   Channel Link ...')
    await state.set_state(states.Event.link)
    
@router.message(states.Event.link, F.text.startswith('https://t.me/'))
async def handler(message: Message, state : FSMContext):
    await state.update_data(link= message.text)
    await message.answer('Chat  Link :    Done  !\nStart   enter   Channel ID ...')
    await state.set_state(states.Event.chat_id)

@router.message(states.Event.chat_id, F.text=='0')
@router.message(states.Event.chat_id, F.text.isdigit())
async def handler(message: Message, state : FSMContext):
    chat_id= message.text if message.text !='0' else None
    await state.update_data(chat_id= chat_id)
    await message.answer('Channel  Id :    {}  !\nStart   enter   Prizes ...'.format('Done' if chat_id else 'Skipped'))
    await state.set_state(states.Event.prizes)
    
@router.message(states.Event.prizes, filters.IsPrizesFormat())
async def handler(message: Message, state : FSMContext):
    await state.update_data(prizes= message.text)
    await message.answer('Prizes :    Done  !\nStart   enter   Time...')
    await state.set_state(states.Event.time)
    
@router.message(states.Event.time, filters.IsDateTimeFormat())
async def handler(message: Message, state : FSMContext, dt):
    await message.answer(f'Time :    Done  !\nEvent  ends  at   {str(dt)[:-10]}\n\nCreate  an  event ? ', reply_markup=kb.create_long_confirmation())
    await state.update_data(time= dt, confirmation_value= 2)

@router.callback_query(states.Event.time, F.data=='long_confirmation')
async def handler(callback : CallbackQuery, state: FSMContext):
    data = asdataclass(**(await state.get_data()))
    await callback.answer(f'{data.confirmation_value}')
    await state.update_data(confirmation_value = data.confirmation_value-1)
    if data.confirmation_value == 0:
        del data.confirmation_value
        await rq.set_event(vars(data))
        total = tools.set_event(callback.message.bot, data)
        await callback.message.edit_text(f'❕❕  [ {total} ]  users  got  a  message!\n\nEvent   ends   at   [ {str(data.time)[:-10]} ]')
        await state.set_state()
    
    
# баланс
@router.callback_query(F.data == 'panel__set_balance')
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text('⌨️  Set  Balance.   Start  writing  tg  id  ...', reply_markup=kb.close())
    await state.set_state(states.Balance.tg_id)
    
@router.message(states.Balance.tg_id, filters.IsDBUser())
async def handler(message: Message, state : FSMContext, user):
    await state.update_data(balance = user.balance, tg_id=user.tg_id)
    await message.answer(f'💷 [ {user.tg_id} ]  user  has  [ {user.balance}  uc ]\nPlease,   enter   ammount ...')
    await state.set_state(states.Balance.amount)

@router.message(states.Balance.amount, F.text.isdigit())
async def handler(message: Message, state : FSMContext):
    data = asdataclass(**(await state.get_data()))
    await rq.set_balance(data.tg_id, int(message.text))    
    await message.answer(f'💷 Done !  [ {data.tg_id} ]  user  has  [ {message.text}  uc ]', reply_markup=kb.cancel(f'balance:{data.tg_id}:{data.balance}'))
    await state.set_state()

@router.callback_query(F.data.startswith('сancel__balance'))
async def handler(callback : CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f'<s>{callback.message.text}</s>')
    data = callback.data.split(":")[1:]
    await rq.set_balance(*data)



        
        
        




@router.callback_query(F.data == 'in_chat')
async def handler(callback : CallbackQuery, state: FSMContext):
    pass




#Main menu


#Profile
@router.message(F.text == '🐵 Профиль')
async def profile(message: Message, state: FSMContext, session: AsyncSession):
    tg_id = message.from_user.id

    user = await rq.get_user(tg_id, session)

    withdrawal_stat = await rq.get_stat_withdrawal(session)

    if withdrawal_stat:
        bot_withdrawal_count = withdrawal_stat.bot_withdrawal_count
        bot_withdrawal_sum = withdrawal_stat.bot_withdrawal_sum
    else:
        bot_withdrawal_count = 0
        bot_withdrawal_sum = 0

    balance = user.balance
    completed_tasks_count = user.task_completed
    lvl = user.lvl
    taked_achievements_count = await rq.get_achievements_count(tg_id, session)
    tg_bot_link = 'https://t.me/koshmrUCbot'
    refferals_count = await rq.get_referral_count_by_tg_id(tg_id, session)
    earned_by_refferals = user.referral_earnings
    count_of_withdrawal = bot_withdrawal_count
    withdrawal_sum = bot_withdrawal_sum

    info_message = f"""
    🐵 Ваш профиль:

Информация в боте:
🆔 Ваш TG ID: {tg_id}
💰 Ваш баланс: {balance} UC
📋 Выполнено заданий: {completed_tasks_count} шт.

Информация о прокачке:
🥇 Ваш Уровень: {lvl}
🏅 Получено достижений: {taked_achievements_count}

Информация о рефералах:
🌟 Пригласи друга и получи целых 2 UC в придачу!
🔗 Ваша реферальная ссылка: {tg_bot_link}?start={tg_id}
👥 Приглашено рефералов: {refferals_count}
💵 Заработано с рефералов: {earned_by_refferals} UC

Информация о выводах:
✨ Количество выводов: {count_of_withdrawal}
🪙 На сумму: {withdrawal_sum} UC
    """

    await message.answer(text=info_message, reply_markup= kb.back_to_profile_kb())



@router.callback_query(F.data == 'back_to_profile')
async def back_to_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.answer('Вы были перемещены в меню.', reply_markup= await kb.main_keyboard(callback.from_user.id, session))





@router.callback_query(F.data.startswith("task_"))
async def task_handler(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    
    task = await rq.get_task_by_id(task_id) 
    if task:
        task_name = task.name 
        task_execute_limit = task.execute_limit
        task_reward = task.reward 
        task_channel_link = task.channel_link 
        left_time = task.left_time #TODO FIX

        task_description = f"""
        📋 Задание #{task_id}

        📄 Имя задания: {task_name}
        """

        if task.category != "TIME":
            task_description += f"🗒 Количество выполнений: {task_execute_limit}n"
        else:
            task_description += f"⌛️ Истекает через: {left_time}n"

        task_description += f"💵 Награда за задание: {task_reward}nn" 
        task_description += "⚠️ Примечание! В случае, если вы отпишетесь от канала после выполнения задания, вы можете быть оштрафованы на сумму, которая была выдана в виде награды. Баланс может уйти в минус, будьте внимательны.nn"

        keyboard = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(text="🔗 Ссылка на канал", url=task_channel_link),
            InlineKeyboardButton(text="✅ Проверить", callback_data=f"check_{task_id}"),
            InlineKeyboardButton(text="🔙 Обратно", callback_data=f"back_{task_id}")
        )

        await callback.message.edit_text(task_description, reply_markup=keyboard)
    else:
        await callback.message.edit_text("❌ Задание не найдено")     

@router.callback_query(F.data.startswith("check_"))
async def check_handler(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    task = await rq.get_task_by_id(task_id)
    if task:
        is_subscribed = await tools.check_channel_sub(callback.from_user.id, task.channel_id) 
        if is_subscribed:
            await callback.message.edit_text("✅ Вы подписаны на канал!", reply_markup=kb.profile_kb())
            try:
                await rq.add_balance(tg_id=callback.from_user.id, amount=task.reward)
                achievement_added = await rq.add_achievement(tg_id=callback.from_user.id,achievement_name='Это только начало!')
                if achievement_added:
                    achievement_message = (
                        f"Поздравляю, вы получили достижение!\n\n"
                        f"**Название:** Это только начало!\n"
                        f"**Описание:** Вы успешно выполнили свое первое задание!\n\n"
                        f"**Награда:** 2UC \n"
                        f"**Как получить:** Выполнить одно задание"
                    )
                    await rq.add_balance(tg_id=callback.from_user.id, amount=2)

                    await callback.message.answer(achievement_message, reply_markup=kb.back_to_profile_kb())

            except Exception as e:
                Logger.error(e)
        else:
            await callback.message.edit_text("❌ Вы не подписаны на канал!", reply_markup=kb.profile_kb())

@router.callback_query(F.data.startswith("back_"))
async def back_handler(callback: CallbackQuery):
    await tasks_handler(callback.message)

@router.message(lambda message: message.text == '🏆 ТОП')
async def show_leaderboard(message: Message, state: FSMContext, session: AsyncSession):
    leaderboard = await rq.get_top_users(limit=10,session=session)
    user = await rq.get_user(message.from_user.id,session)

    if not user:
        await message.answer("⚠️ Ошибка при получении данных пользователя.")
        return

    leaderboard_text = "🥇 Топ 10 пользователей:\n\n"

    if not leaderboard:
        leaderboard_text += "Список пуст. Станьте первым!\n\n"
    else:
        for i, (user_id, full_name, task_count) in enumerate(leaderboard, 1):
            clean_name = full_name or "Неизвестный"
            leaderboard_text += f"{i}# {clean_name} - {task_count} заданий\n"

    user_rank =  await rq.get_user_top_position(user.id,session)
    if user_rank:
        if user.is_hidden:
            leaderboard_text += f"\nВаше место в топе: (Вы скрыли себя)"
        else:
            leaderboard_text += f"\nВаше место в топе: {user_rank}"
    else:
        leaderboard_text += "\nВаше место в топе: (Вне рейтинга)"

    button_text = "🙈 Скрыть меня" if not user.is_hidden else "🐵 Показать меня"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="toggle_visibility")]
        ]
    )

    await message.answer(text=leaderboard_text, reply_markup=keyboard)
    session.close()


@router.callback_query(lambda c: c.data == 'toggle_visibility')
async def toggle_user_visibility(callback: CallbackQuery, session: AsyncSession):
    user = await rq.get_user(callback.from_user.id,session)

    if not user:
        await bot.answer_callback_query(callback.id, "⚠️ Ошибка при получении данных пользователя.")
        return

    user.is_hidden = not user.is_hidden


    leaderboard = await rq.get_top_users(limit=10,session=session)
    leaderboard_text = "🏆 Топ 10 пользователей:\n\n"

    if not leaderboard:
        leaderboard_text += "Список пуст. Станьте первым!\n\n"
    else:
        for i, (user_id, full_name, task_count) in enumerate(leaderboard, 1):
            clean_name = full_name or "Неизвестный"
            leaderboard_text += f"{i}# {clean_name} - {task_count} заданий\n"

    user_rank =  await rq.get_user_top_position(user.id,session)
    if user_rank:
        if user.is_hidden:
            leaderboard_text += f"\nВаше место в топе: (Вы скрыли себя)"
        else:
            leaderboard_text += f"\nВаше место в топе: {user_rank}"
    else:
        leaderboard_text += "\nВаше место в топе: (Вне рейтинга)"

    button_text = "🙈 Скрыть меня" if not user.is_hidden else "🐵 Показать меня"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="toggle_visibility")]
        ]
    )

    await bot.edit_message_text(
        text=leaderboard_text,
        chat_id=str(callback.message.chat.id),
        message_id=callback.message.message_id,
        reply_markup=keyboard
    )
    await bot.answer_callback_query(callback.id, "Ваша видимость в топе изменена.")
    session.close()


@router.message(F.text == '💸 Вывод UC')
async def withdrawal_uc(message: Message, session: AsyncSession):

    user = await rq.user(message.from_user.id, session)
    if user.balance < 60:
        await message.answer('Минимальная сумма вывода: <b>60 UC</b>', parse_mode='HTML', reply_markup=kb.back_to_profile_kb())
    elif user.balance >= 60:
        withdrawal_stat = await rq.get_stat_withdrawal(session)

        if withdrawal_stat:
            bot_withdrawal_count = withdrawal_stat.bot_withdrawal_count
            bot_withdrawal_sum = withdrawal_stat.bot_withdrawal_sum
        else:
            bot_withdrawal_count = 0
            bot_withdrawal_sum = 0

        message_text = (
            '💸 Вы можете вывести 60 UC в виде кода активации. Для этого нажмите кнопку ниже.'
            '\n📊 Статистика выводов в боте:'
            '\n- ✨ Количество выводов: {bot_withdrawal_count}'
            '\n- 💵 На сумму: {bot_withdrawal_sum} UC'
        ).format(bot_withdrawal_count=bot_withdrawal_count, bot_withdrawal_sum=bot_withdrawal_sum) 


        await message.answer(text=message_text, reply_markup=kb.uc_count())


@router.callback_query(F.data == 'withdrawal_uc')
async def withdrawal_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user = await rq.get_user_by_id(callback.from_user.id)
    if user.balance >= 60:
        code = await rq.get_activation_code()
        if code:
            await rq.set_balance(callback.from_user.id, user.balance - 60, session)
            await rq.update_withdrawal_stat()
            await callback.message.edit_text(
                f"""
                ✅ Вывод успешно выполнен!

                🗝 Ваш Код Активации: {code}

                ℹ️ Инструкция по активации: https://vk.cc/cyfkVG

                ✨ Оставьте отзыв и получите уже первое достижение с наградой!
                👇 Напишите ваши впечатления о боте и о правдивости работы бота и он попадет в наш чат с отзывами:
                """,
                reply_markup=kb.review_kb() 
            )
            await state.set_state(states.ReviewState.review_text)
        else:
            await callback.message.edit_text("❌ Ошибка получения кода. Попробуйте позже.")
    else:
        await callback.message.edit_text('❌ Недостаточно средств.', reply_markup=kb.back_to_profile_kb())


@router.message(states.ReviewState.review_text)
async def process_review(message: Message, state: FSMContext):
    if len(message.text) > 128 or len(message.text.replace(" ", "").replace(",", "").replace(".", "")) > 128 - 4:
        await message.answer('Отзыв слишком длинный. Сократите его до 128 символов', reply_markup=kb.back_to_profile_kb())
        await state.clear()
    else:
        await state.update_data(review_text=message.text)
        await message.answer(
            f"""
            ✍️ Ваш отзыв:
            {message.text}

            ⚠️ Учтите! Отправка отзыва с матерными словами, содержащий бессмысленные символы или большое количество эмодзи, будут удалены и у вас будет риск получить штрафы до 60 UC.
            """,
            reply_markup=kb.confirm_review_kb()
        )


@router.callback_query(F.data == 'confirm_review')
async def confirm_review_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    review_text = data.get('review_text')
    if review_text:
        user = await rq.user(callback.from_user.id)
        username = user.username 

        await bot.send_message(chat_id="-1002228388262", text=f"Отзыв от {username}:\n{review_text}")
        await callback.message.edit_text(
            "✅ Отзыв успешно отправлен!", reply_markup=kb.profile_kb() 
        )
        achievement_added = await rq.add_achievement(tg_id=callback.from_user.id, achievement_name='Ха-Ха, вот и я со своим мнением!')
        if achievement_added:
                achievement_message = (
                    f"Поздравляю, вы получили достижение!\n\n"
                    f"**Название:** Ха-Ха, вот и я со своим мнением!\n"
                    f"**Описание:** Вы успешно оставили свой первый отзыв.\n\n"
                    f"**Награда:** 2UC \n"
                    f"**Как получить:** Успешно оставить отзыв"
                )
                await rq.add_balance(tg_id=callback.from_user.id, amount=2)

                await callback.message.answer(achievement_message, reply_markup=kb.back_to_profile_kb())
        await state.clear()
    else:
        await callback.message.edit_text("❌ Ошибка отправки отзыва. Попробуйте позже.")
        await state.clear()


@router.callback_query(F.data == 'cancel_review')
async def cancel_review_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отправка отзыва отменена.", reply_markup=kb.profile_kb())
    await state.clear()

@router.callback_query(F.data == 'dont_leave_review')
async def dont_leave_review_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Вы не оставили отзыв.", reply_markup=kb.profile_kb())
    await state.clear()


@router.message(F.text == '🎲Мини-игры')
async def mini_games(message: Message):
    await message.answer('Выберите мини-игру', reply_markup=kb.games())


@router.callback_query(F.data == 'dice')
async def dice(callback: CallbackQuery):
    message_dice = """<b>Правила игры в кости</b>
                    \n- Каждый игрок бросает кубик.
                    \n- Выигрывает игрок, у которого выпало наибольшее число очков.
                    \n- В случае ничьей, победителя нет.
                    """
    await callback.message.edit_text(text=message_dice, parse_mode='HTML', reply_markup=kb.bet())


# @router.callback_query(lambda c: c.data in ['5', '30', '60'])
# async def process_bet(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
#     try:
#         bet_amount = int(callback.data)
#         tg_id = callback.from_user.id

#         user_status = await rq.get_user_status(tg_id, session)

#         if user_status == 'waiting_opponent':
#             await callback.answer('Вы уже ищете противника. Пожалуйста, дождитесь завершения текущей игры.', show_alert=True)
#             return
#         elif user_status == 'in_game':
#             await callback.answer('Вы уже находитесь в активной игре. Пожалуйста, дождитесь ее завершения.', show_alert=True)
#             return

#         user_balance = await rq.get_balance(tg_id, session)

#         if user_balance < bet_amount:
#             await callback.answer('У вас недостаточно средств для этой ставки.', show_alert=True)
#             return

#         await state.set_state(states.GameStates.waiting_opponent)
#         await rq.start_game(tg_id, wait_game=True, bet_amount=bet_amount, session=session)

#         await callback.answer('Поиск противника...')

#         timeout = 30
#         start_time = time.monotonic()
#         while time.monotonic() - start_time < timeout:
#             opponent_tg_id = await rq.find_opp(tg_id, bet_amount, session)
#             if opponent_tg_id:
#                 break
#             await asyncio.sleep(1)

#         if opponent_tg_id:
#             player1_roll, player2_roll = await roll_dice()

#             if player1_roll > player2_roll:
#                 await rq.add_balance(tg_id, bet_amount, session)
#                 winner_message = 'Поздравляем, вы выиграли!'
#                 loser_message = 'К сожалению, вы проиграли.'
#             elif player1_roll < player2_roll:
#                 await rq.add_balance(opponent_tg_id, bet_amount, session)
#                 winner_message = 'К сожалению, вы проиграли.'
#                 loser_message = 'Поздравляем, вы выиграли!'
#             else:
#                 winner_message = 'Ничья!'
#                 loser_message = 'Ничья!'

#             updated_balance = await rq.get_balance(tg_id, session)

#             result_message = (f'{winner_message}\n\n'
#                               f'Ваш бросок: {player1_roll}\n'
#                               f'Бросок соперника: {player2_roll}\n\n'
#                               f'Ваш текущий баланс: <code>{updated_balance}</code>')

#             await bot.send_message(chat_id=tg_id, text=result_message, parse_mode='HTML')
#             await bot.send_message(chat_id=opponent_tg_id, text=loser_message, parse_mode='HTML')

#             await rq.start_game(tg_id, wait_game=False, bet_amount=bet_amount, session=session)
#             await rq.start_game(opponent_tg_id, wait_game=False, bet_amount=bet_amount, session=session)

#             await rq.update_user_status(tg_id, 'idle', session=session)
#             await rq.update_user_status(opponent_tg_id, 'idle', session=session)

#             await state.clear()

#         else:
#             await callback.message.answer('Противник не найден, игра отменена.')
#             await rq.update_user_status(tg_id, 'idle', session=session)
#             await state.clear()

#     except Exception as e:
#         print(e)

# async def roll_dice():
#     player1_roll = randint(1, 6)
#     player2_roll = randint(1, 6)
#     return player1_roll, player2_roll



@router.message(F.text == '❓ Ответы на вопросы')
async def faq(message: Message, session: AsyncSession):
    faq_message = """<b>❓ Привет! Здесь вы найдете ответы на часто задаваемые вопросы:</b>

1️⃣ <b>Вопрос:</b> Почему я пригласил друга, а мне не зачислили награду?
   🔹 <b>Ответ:</b> Приглашенные вами люди должны выполнить обязательные задания, чтобы вы, как реферер, получили свою награду. В противном случае увеличивается только счетчик приглашенных. Поэтому, когда приглашаете друзей, обязательно напомните им о необходимости выполнения первых простых заданий.

2️⃣ <b>Вопрос:</b> В профиле указан не мой ID от PUBG Mobile. Почему? Как его поменять?
   🔹 <b>Ответ:</b> ID, указанный в профиле, это ID вашего аккаунта в Telegram. Мы используем его для идентификации вас, отображения профиля и решения возможных проблем.

3️⃣ <b>Вопрос:</b> Почему при нажатии на "Проверить" появляется сообщение, что задание не найдено?
   🔹 <b>Ответ:</b> Сообщение "Задание не найдено" обычно означает, что задание завершено. В некоторых случаях это может значить, что администратор бота удалил задание, и оно больше не доступно.

4️⃣ <b>Вопрос:</b> Как вывести UC из бота?
   🔹 <b>Ответ:</b> После накопления необходимой суммы UC на вашем балансе, вы можете вывести их. Для этого нажмите на кнопку "Вывести" и следуйте инструкциям. После вывода вы получите код активации и ссылку на инструкцию по выводу.

<b>Если у вас остались вопросы, не стесняйтесь обращаться к администрации.</b>"""
    
    await message.answer(faq_message, parse_mode='HTML', reply_markup=kb.back_to_profile_kb())