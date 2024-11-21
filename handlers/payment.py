from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loguru import logger


from utils import get_text, create_invoice
from crud import db_api
from app import dp


payment_cb = CallbackData('payment', 'name', 'action')


class Payment(StatesGroup):
    amount = State()


@dp.callback_query_handler(lambda x: x.data == 'Pay_Back', state="*")
async def process_category_back(callback: CallbackQuery, state: FSMContext):
    await payment(callback.message, state)


@logger.catch
@dp.message_handler(regexp='.*Пополнить|.*Top up')
async def payment(message: Message, state: FSMContext):
    tg_id = message.chat.id
    current_language = await db_api.get_user_language(tg_id)
    text = get_text('way', current_language)
    back = get_text('back', current_language)
    keyboard = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton("☁️CryptoCloud (recomended)", callback_data="CryptoCloud")
    button4 = InlineKeyboardButton(back, callback_data='Back')
    keyboard.add(button1)
    keyboard.add(button4)
    await message.answer(text, reply_markup=keyboard)
    logger.debug(f'User {tg_id} user_start_payment: {text}')


@logger.catch
@dp.callback_query_handler(lambda c: c.data == "CryptoCloud", state="*")
async def crypto_cloud_payment(query: CallbackQuery, state: FSMContext):
    tg_id = query.from_user.id
    logger.debug(f'User {tg_id} user_start_payment: CryptoCloud.')
    current_language = await db_api.get_user_language(tg_id)
    text = get_text('count1', current_language)
    back = get_text('back', current_language)
    keyboard = InlineKeyboardMarkup(row_width=1)
    button4 = InlineKeyboardButton(back, callback_data='Pay_Back')
    keyboard.add(button4)
    await Payment.amount.set()
    await query.message.answer(text, reply_markup=keyboard)
    logger.info(f'User {tg_id}: amount_payment, data: {query.data}')


@logger.catch
@dp.message_handler(state=Payment.amount)
async def process_payment(message: Message, state: FSMContext):
    tg_id = message.from_id
    current_language = await db_api.get_user_language(tg_id)
    try:
        amount = float(message.text)
        if amount < 0:
            await message.answer(get_text("incorrect quantity", current_language))
        else:
            async with state.proxy() as data:
                data['amount'] = amount
            invoice = await create_invoice(amount)

        if invoice['status'] == 'success':

            link = invoice['result']['link']
            uuid = invoice['result']['uuid']
            await db_api.add_cryptocloud_payment(tg_id, amount, uuid)
            text = get_text('pay_link', current_language)
            mess = text + '\n' + link

            logger.info(f'User {tg_id}: process_payment, uuid: {uuid}, payment_amount: {amount}, message: {mess}')
        else:
            mess = "The server is temporarily unavailable. Please try again later."

        back = get_text('back', current_language)
        keyboard = InlineKeyboardMarkup(row_width=1)
        button4 = InlineKeyboardButton(back, callback_data='Pay_Back')
        keyboard.add(button4)
        await message.answer(mess, reply_markup=keyboard)

    except ValueError:
        from .keyboard_exept import submit_cheker
        await submit_cheker(message, state, current_language)
    await state.finish()
