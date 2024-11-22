import asyncio

import aiofiles
from loguru import logger
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app import dp
from filters import IsAdmin
from crud import admins, users
from utils import process_users, bot_send_message, process_orders
from keyboards import (cancel_message, confirm_message, mass_letters, users_log, add_cat, admin_markup,
                       confirm_markup, cancel_markup, user_balance, user_orders)


class Sending(StatesGroup):
    message_submit = State()
    message_send = State()


class NewUsers(StatesGroup):
    offset_submit = State()


class Logs(StatesGroup):
    offset_submit = State()


class CategoryState(StatesGroup):
    mark = State()
    country = State()
    type = State()
    model = State()
    confirm = State()


class UserBalance(StatesGroup):
    username = State()
    amount = State()
    confirm = State()


class UserOrders(StatesGroup):
    username = State()


@logger.catch
@dp.message_handler(IsAdmin(), commands="admin")
async def admin_start(message: Message):
    await message.reply('Hello, Admin!', reply_markup=admin_markup)
    logger.warning(f'User {message.from_user.id} включил админку')


@logger.catch
@dp.message_handler(IsAdmin(), text=user_balance)
async def start_user_balance(message: Message):
    await message.reply('Введи username пользователя в формате @User.', reply_markup=cancel_markup)
    await UserBalance.username.set()


@logger.catch
@dp.message_handler(IsAdmin(), state=UserBalance.username)
async def set_username(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text.replace('@', '', 1)
    await UserBalance.next()
    await message.answer('Введи сумму пополения в $.', reply_markup=cancel_markup)


@logger.catch
@dp.message_handler(IsAdmin(), state=UserBalance.amount)
async def set_usd_amount(message: Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['amount'] = float(message.text)
            username = data['username']
        user_info = await users.get_user_by_username(username)
        if user_info:
            async with state.proxy() as data:
                data['tg_id'] = user_info.tg_id
                data['balance'] = float(user_info.balance)
            await message.answer(f"Пользователь {data['tg_id']}: {username}\nТекущий баланс: {data['balance']}\nСумма пополнения: {data['amount']}", reply_markup=confirm_markup)
            await UserBalance.next()
        else:
            await message.answer('Пользователя с таким username нет в базе!', reply_markup=admin_markup)

    except ValueError:
        if message.text == cancel_message:
            await message.answer('❌Отменено', reply_markup=admin_markup)
        else:
            await message.answer('Неверное значение! Попробуй снова.', reply_markup=admin_markup)
        await state.finish()


@logger.catch
@dp.message_handler(IsAdmin(), text=confirm_message, state=UserBalance.confirm)
async def admin_update_user_balance(message: Message, state: FSMContext):
    async with state.proxy() as data:
        tg_id = data['tg_id']
        balance = data['balance']
        amount = data['amount']
    new_balance = balance + amount
    await users.update_user_balance(tg_id, new_balance)
    await message.answer('👌Баланс пополнен!', reply_markup=admin_markup)
    await state.finish()
    logger.info(f'User {message.from_user.id} пополнил баланс пользователя {tg_id} на {amount}$.')


@logger.catch
@dp.message_handler(IsAdmin(), text=mass_letters)
async def send_message(message: Message):
    await message.answer('Введи сообщение для рассылки всем пользователям.', reply_markup=cancel_markup)
    await Sending.message_submit.set()
    logger.info(f'User {message.from_user.id} пишет сообщение {message.text}')


@logger.catch
@dp.message_handler(IsAdmin(), text=cancel_message, state="*")
async def process_send_cancel(message: Message, state: FSMContext):
    await state.finish()
    await message.answer('❌Отменено', reply_markup=admin_markup)
    logger.info(f'User {message.from_user.id} отменил отправку.')


@logger.catch
@dp.message_handler(IsAdmin(), state=Sending.message_submit)
async def submit_send(message: Message, state: FSMContext):
    await state.update_data(message1=message.text)
    await message.answer(f'Отправить всем? \n"{message.text}"', reply_markup=confirm_markup)
    await Sending.message_send.set()
    logger.info(f'User {message.from_user.id} отправил всем сообщение: {message.text}')


@logger.catch
@dp.message_handler(IsAdmin(), text=confirm_message, state=Sending.message_send)
async def process_send(message: Message, state: FSMContext):
    users_ = await users.get_all_unblock_users()
    mess = await state.get_data('message1')
    mess_text = str(mess['message1'])
    tasks = [asyncio.create_task(bot_send_message(user.tg_id, mess_text)) for user in users_]
    await asyncio.gather(*tasks)
    await state.finish()
    await message.answer("Сообщение отправлено!", reply_markup=admin_markup)
    logger.info(f'Количество сообщений: {len(tasks)}')


@logger.catch
@dp.message_handler(IsAdmin(), text=users_log)
async def new_users(message: Message):
    await message.answer('Введи промежуток в днях, за который ты хочешь получить отчёт.', reply_markup=cancel_markup)
    await NewUsers.offset_submit.set()


@logger.catch
@dp.message_handler(IsAdmin(), state=NewUsers.offset_submit)
async def send_new_users(message: Message, state: FSMContext):
    offset = int(message.text)
    await state.finish()
    users_ = await admins.get_new_users(offset)
    path = await process_users(users_)
    text = 'Новые пользователи.'
    async with aiofiles.open(path, 'rb') as file:
        await message.answer_document(document=file)
    await message.answer(text, reply_markup=admin_markup)
    logger.info(f'User {message.from_user.id} получает всех новых пользователей: {path}.')


@logger.catch
@dp.message_handler(IsAdmin(), text=add_cat)
async def add_title_category(message: Message):
    await CategoryState.mark.set()
    await message.answer('Марка?', reply_markup=cancel_markup)


@logger.catch
@dp.message_handler(IsAdmin(), state=CategoryState.mark)
async def set_category_title_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['mark'] = message.text
    await CategoryState.next()
    await message.answer('Страна-производитель?', reply_markup=cancel_markup)


@logger.catch
@dp.message_handler(IsAdmin(), state=CategoryState.country)
async def set_category_title_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['country'] = message.text
    await CategoryState.next()
    await message.answer('Класс мотоцикла?', reply_markup=cancel_markup)


@logger.catch
@dp.message_handler(IsAdmin(), state=CategoryState.type)
async def set_type_title_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = message.text
    await CategoryState.next()
    await message.answer('Модель?', reply_markup=cancel_markup)


@logger.catch
@dp.message_handler(IsAdmin(), state=CategoryState.model)
async def set_country_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['model'] = message.text
        country = data['country']
        mark = data['mark']
        type = data['type']
    text = f'Добавить товар?\nМарка: {mark}\nСтрана: {country}\nКласс мотоцикла: {type}\nМодель: {message.text}\n'
    await CategoryState.next()
    await message.answer(text, reply_markup=confirm_markup)


@logger.catch
@dp.message_handler(IsAdmin(), text=confirm_message, state=CategoryState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        mark = data['mark']
        country = data['country']
        type = data['type']
        model = data['model']
    exist = await admins.get_category(mark)
    if exist is None:
        await admins.add_category(mark, country)
    await admins.add_catalog(mark, type, model)
    await message.answer('👌Товар добавлен!', reply_markup=admin_markup)
    await state.finish()
    text = f'\nМарка: {mark}\nСтрана: {country}\nКласс мотоцикла: {type}\nМодель: {model}\n'
    logger.info(f'User {message.from_user.id} добавил категорию: {text}.')


@logger.catch
@dp.message_handler(IsAdmin(), text=user_orders)
async def get_user_orders(message: Message):
    await message.reply('Введи username пользователя в формате @User.', reply_markup=cancel_markup)
    await UserOrders.username.set()


@logger.catch
@dp.message_handler(IsAdmin(), state=UserOrders.username)
async def set_username_orders(message: Message, state: FSMContext):
    username = message.text.replace('@', '', 1)
    user_orders = await admins.get_user_orders(username)
    await state.finish()
    if user_orders:
        path = await process_orders(username, user_orders)
        async with aiofiles.open(path, 'rb') as file:
            await message.answer_document(document=file)
        await message.answer(f"Заказы пользователя @{username}", reply_markup=admin_markup)
        logger.info(f'User {message.from_user.id} получает заказы пользователя {username}: {path}.')
    else:
        await message.answer('Пользователя с таким username нет в базе!', reply_markup=admin_markup)
