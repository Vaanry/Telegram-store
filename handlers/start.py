from pathlib import Path

from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, ChatMemberUpdated
import aiofiles
from loguru import logger

from crud import catalogs, users
from app import dp
from utils import get_text, is_promo_active


BASE_DIR = Path(__file__).resolve().parent.parent

logger.remove()
logger.add(
    f'{BASE_DIR}/logs/user_handlers.log',
    rotation="1000 MB",
    retention="90 days",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {file}:{line} | {message}",
    level="DEBUG",
    catch=True
)


@logger.catch
@dp.message_handler(commands='start')
async def cmd_start(message: Message):
    await catalogs.start_count_data()
    tg_id = message.chat.id
    user_info = await users.get_user(tg_id)
    if user_info is False:
        username = message.from_user.username
        args = message.get_args()
        if args:
            source = args.split('-')[1]
        else:
            source = None
        await users.add_user(tg_id, username, source)
        logger.info(f'User {tg_id} зарегистрировался, источник - {source}')
        user_info = await users.get_user(tg_id)
    balance = user_info.balance
    current_language = user_info.language
    text = get_text('greeting', current_language)
    catalog = get_text('catalog', current_language)
    pay = get_text('balance', current_language)
    rows = await catalogs.give_all_rows()

    if current_language == 'en':
        bal = f"💰Your balance: {balance}$"
        stock = f'{rows} motorbikes🏍'
    else:
        bal = f"💰Твой баланс: {balance}$"
        stock = f'{rows} мотоциклов🏍'

    mess = f'{text}{stock}\n\n{bal}'
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    catalog_b = KeyboardButton(catalog)
    switch_b = KeyboardButton("🇷🇺RU/EN🇺🇸")
    pay_b = KeyboardButton(pay)
    about = get_text('about', current_language)
    markup.add(catalog_b, switch_b, pay_b, about)
    await message.answer(mess, reply_markup=markup)
    logger.info(f'User {tg_id} запустил бота')


@logger.catch
@dp.message_handler(text="🇷🇺RU/EN🇺🇸")
async def switch_language(message: Message):
    tg_id = message.chat.id
    current_language = await users.get_user_language(tg_id)
    if current_language == 'en':
        new_lang = 'ru'
    else:
        new_lang = 'en'
    await users.update_user_language(tg_id, new_lang)
    text = get_text('switch', new_lang)
    await message.answer(text,
                         reply_markup=ReplyKeyboardRemove())
    logger.info(f'User {tg_id} сменил язык на {new_lang}')


@logger.catch
@dp.message_handler(commands='help')
async def user_help(message: Message):
    mess = '''По особым запросам обращайтесь к администратору:
@username
For special requests, please contact the administrator:
@username
'''
    await message.reply(mess)


@logger.catch
@dp.message_handler(regexp='.*О нас|.*About us')
async def about(message: Message):
    tg_id = message.chat.id
    current_language = await users.get_user_language(tg_id)
    text = get_text('about_descr', current_language)
    await message.answer(text)


@logger.catch
@dp.message_handler(commands='free')
async def cmd_free(message: Message):
    tg_id = message.chat.id
    current_language = await users.get_user_language(tg_id)
    status = await is_promo_active(tg_id)
    logger.info(f'User {tg_id} жмёт free')
    if status == 'No promo':
        text = get_text('No promo', current_language)
        await message.answer(text)
    elif status == 'Expired':
        text = get_text('Expired', current_language)
        await message.answer(text)
    else:
        text = get_text('Take free', current_language)
        async with aiofiles.open(status, 'rb') as file:
            await message.answer_document(document=file)
        await message.answer(text)
        logger.info(f'User {tg_id} получил free')


@logger.catch
@dp.my_chat_member_handler()
async def my_chat_member_handler(message: ChatMemberUpdated):
    tg_id = message.chat.id
    if message.chat.type == 'private':
        if message.new_chat_member.status == "kicked":
            await users.update_block_bot_status(tg_id, True)
            logger.info(f'User {tg_id} заблокировал бота')
        elif message.new_chat_member.status == "member":
            await users.update_block_bot_status(tg_id, False)
            logger.info(f'User {tg_id} разблокировал бота')
