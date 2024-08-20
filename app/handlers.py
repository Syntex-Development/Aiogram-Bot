from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from textwrap import dedent as dd
from types import SimpleNamespace as asdataclass


from app.middlewares import TestMiddleware1, TestMiddleware2
from config import config
from . import filters
from . import states
import app.resources.tools as tools
import app.database.requests as rq 
import app.keyboards as kb

import logging



router = Router()
router.callback_query.outer_middleware(TestMiddleware1())
router.message.outer_middleware(TestMiddleware2())


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
@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery, state: FSMContext):

    #TODO: Подставить значения из БД!
    tg_id = ... # получить TG ID из базы данных 
    balance = ... # получить баланс из базы данных 
    completed_tasks_count = ... # получить количество выполненных заданий из базы данных
    lvl = ... # получить уровень из базы данных
    taked_achievements_count = ... # получить количество полученных достижений из базы данных 
    tg_bot_link = ... # получить ссылку на бота
    refferals_count = ... # получить количество рефералов из базы данных
    earned_by_refferals = ... # получить заработок с рефералов из базы данных
    count_of_withdrawal = ... # получить количество выводов из базы данных
    withdrawal_sum = ... # получить сумму выводов из базы данных

    info_message = f"""
    🐵 **Ваш профиль:**

    **Информация в боте:**
    🆔 **Ваш TG ID:** {tg_id}
    💰 **Ваш баланс:** {balance} UC
    📋 **Выполнено заданий:** {completed_tasks_count} шт.

    **Информация о прокачке:**
    🥇 **Ваш Уровень:** {lvl}
    🏅 **Получено достижений:** {taked_achievements_count}

    **Информация о рефералах:**
    🌟 **Пригласи друга и получи целых 2 UC в придачу!**
    🔗 **Ваша реферальная ссылка:** {tg_bot_link}?start={tg_id}
    👥 **Приглашено рефералов:** {refferals_count}
    💵 **Заработано с рефералов:** +{earned_by_refferals} UC

    **Информация о выводах:**
    ✨ **Количество выводов:** {count_of_withdrawal}
    🪙 **На сумму:** {withdrawal_sum} UC
    """

    await callback.edit_text(text=info_message,reply_markup=kb.profile_kb())


@router.callback_query(F.data == 'achievements')
async def achievement_handler(callback: CallbackQuery, state: FSMContext):
    #TODO: Подставить значения из БД!
    achievements = ... # получить список достижений из базы данных
    achievements_list = "" 

    for achievement in achievements:
        name_achievement = achievement.name # получить название достижения
        achievement_reward = achievement.reward # получить награду за достижение 
        achievement_status = " " if achievement.is_completed else " " # проверить, получено ли достижение 

        achievements_list += f"""
  Достижение: {name_achievement} | Статус: {achievement_status}
        - Награда за получения достижения: {achievement_reward}
        """

    await callback.edit_text(text=f"""
 Список полученных достижений:
    {achievements_list}
    """, reply_markup=kb.back_to_profile_kb())


@router.callback_query(F.data == 'back_to_profile')
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    await profile(callback, state)


@router.callback_query(F.data == 'tasks')
async def tasks_handler(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    message = callback.message
    tasks = await rq.get_tasks(tg_id, message)

    if tasks is False:
        await callback.message.edit_text('❌ В данный момент для вас нет доступных заданий.')
    elif tasks:
        keyboard = InlineKeyboardMarkup(row_width=1)
        for task in tasks:
            keyboard.add(
                InlineKeyboardButton(
                    text=task.name, 
                    callback_data=f"task_{task.id}" 
                )
            )

        await callback.message.edit_text(
            "📋 Вот список доступных заданий для вас:", 
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("task_"))
async def task_handler(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[1])
    
    task = await rq.get_task_by_id(task_id) 
    if task:
        #TODO: ПОДСТАВЬ ЗНАЧЕНИЯ ИЗ БАЗЫ ДАННЫХ.
        task_name = task.name 
        task_execute_limit = task.execute_limit
        task_reward = task.reward 
        task_channel_link = task.channel_link 
        left_time = task.left_time

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
async def check_handler(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[1])
    task = await rq.get_task_by_id(task_id)
    if task:
        is_subscribed = await tools.check_channel_sub(callback.from_user.id, task.channel_id) 
        if is_subscribed:
            await callback.message.edit_text("✅ Вы подписаны на канал!", reply_markup=kb.profile_kb())
            try:
                rq.add_balance(tg_id=callback.from_user.id, amount=task.reward)
            except Exception as e:
                logging.error(e)
        else:
            await callback.message.edit_text("❌ Вы не подписаны на канал!", reply_markup=kb.profile_kb())

@router.callback_query(F.data.startswith("back_"))
async def back_handler(callback: CallbackQuery, state: FSMContext):
    await tasks_handler(callback, state)