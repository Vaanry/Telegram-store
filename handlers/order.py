import datetime
import os
import asyncio
import aiofiles
import aiofiles.os
from dotenv import load_dotenv
from loguru import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from app import dp
from crud import catalogs, orders, users
from utils import get_text, process_file


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
archive_folder = os.getenv('archives_folder')


@dp.callback_query_handler(lambda x: x.data == 'submit_buy', state="*")
async def process_give(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        age = data.get('age')
        cc = data.get('cc')
        model = data.get('model')

    tg_id = query.from_user.id
    user_info = await users.get_user(tg_id)
    balance = user_info.balance
    current_language = user_info.language
    order_text = get_text('order_text', current_language)

    order = await orders.get_last_order(tg_id)
    is_paid = order.is_paid
    purchase = order.purchase
    amount = order.quantity
    model = order.model

    if is_paid is True:
        await orders.add_order(tg_id, amount, model, purchase, cc, age)

    if float(balance) >= float(purchase):

        rows = await orders.give_order(model, amount, cc, age)
        catalog = get_text('catalog', current_language)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(catalog, callback_data="Back"))

        if len(rows) == 0:
            await query.message.answer(get_text('tovar', current_language), reply_markup=markup)
        else:

            now = datetime.datetime.now()
            date_time = now.strftime("%m_%d_%Y_%H-%M-%S")
            new_dir = str(tg_id) + '_' + date_time
            new_path = os.path.join(archive_folder, new_dir)
            await aiofiles.os.mkdir(new_path)  # создаём архивную папку с заказом пользователя
            await users.update_user_balance(tg_id, float(balance) - float(purchase))
            await orders.update_order(tg_id, new_path)

            tasks = [asyncio.create_task(process_file(path, query, order_text, new_path)) for path in rows]
            await asyncio.gather(*tasks)

            logger.info(f'User {tg_id} приобрёл товар: {new_path}')
            logger.info(f'Баланс User {tg_id} обновлён: {balance - float(purchase)}')

            await query.message.answer('🤝', reply_markup=markup)
            await catalogs.start_count_data()

    else:
        balance = get_text('balance', current_language)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(balance, callback_data="Pay_Back"))
        no_cash = get_text('funds', current_language)
        await query.message.reply(no_cash, reply_markup=markup)
        logger.info(f'Баланс User {tg_id}: недостаточный баланс')

    await state.finish()
