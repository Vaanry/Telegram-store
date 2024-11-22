import datetime
import asyncio
import os

import aiofiles
import aiofiles.os
import aioshutil
from loguru import logger
from aiocsv import AsyncWriter
from dotenv import load_dotenv
from aiogram.utils.exceptions import RetryAfter, ChatNotFound, BotBlocked, UserDeactivated

from config import bot
from crud import admins, users
from .lexicons import LEXICON

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
logs_path = os.getenv('logs_path')


@logger.catch
def get_text(param: str, lang: str = 'ru') -> str:
    """ get text based on language settings """
    lex = LEXICON[lang]
    return lex.get(param, param)


@logger.catch
def output_format(catalog, quantity, language='en'):
    if language == 'en':
        text = f"""Catalog: {catalog }
Available quantity: {quantity}"""
    else:
        text = f"""Каталог: {catalog }
Доступное количество: {quantity}"""
    return text


@logger.catch
def get_order_format(current_language, amount, purchase, text_format):
    if current_language == 'en':
        submit = '✅ Buy'
        order = f'Your order\n{text_format}\nAmount: {amount}\nPurchase: {purchase}'
    else:
        submit = '✅ Купить'
        order = f'Твой заказ\n{text_format}\nКоличество: {amount}\nСтоимость {purchase}'
    return order, submit


@logger.catch
async def process_file(path, query, order_text, new_path):
    async with aiofiles.open(path, 'rb') as file:
        await query.message.answer_document(document=file, caption=order_text)
    path_existence = await aiofiles.os.path.exists(path)
    if path_existence:
        # await aioshutil.move(path, new_path) prod
        await aioshutil.copy(path, new_path)  # debug


@logger.catch
async def process_logs(logs):
    now = datetime.datetime.now()
    date_time = 'logs_' + now.strftime("%m_%d_%Y_%H-%M")
    filename = os.path.join(logs_path, f'{date_time}.csv')
    columns = ['time', 'id', 'button']
    data = [[log.timestamp.strftime("%m_%d_%Y_%H-%M-%S"), log.tg_id, log.button] for log in logs]
    async with aiofiles.open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = AsyncWriter(file, dialect="unix")
        await writer.writerow(columns)
        await writer.writerows(data)
    return filename


@logger.catch
async def process_users(users):
    now = datetime.datetime.now()
    date_time = 'users_' + now.strftime("%d_%m_%Y_%H-%M")
    filename = os.path.join(logs_path, f'{date_time}.csv')
    columns = ['Id', 'Username', 'Registration date', 'Source']
    data = [[user.tg_id, user.username, user.reg_date.strftime("%d.%m.%Y-%H:%M"), user.source] for user in users]
    async with aiofiles.open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = AsyncWriter(file, dialect="unix")
        await writer.writerow(columns)
        await writer.writerows(data)
    return filename


@logger.catch
async def process_orders(username, user_orders):
    filename = os.path.join(logs_path, f'{username}.csv')
    columns = ['Model', 'Purchase', 'Order archive']
    data = [[order.model, order.purchase, order.order_archive] for order in user_orders]
    async with aiofiles.open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = AsyncWriter(file, dialect="unix")
        await writer.writerow(columns)
        await writer.writerows(data)
    return filename


@logger.catch
async def bot_send_message(tg_id, mess_text):
    try:
        await bot.send_message(tg_id, mess_text)
    except RetryAfter as e:
        logger.error(f"Задержка отправки {tg_id} на {e.timeout}")
        await asyncio.sleep(e.timeout)
        await bot_send_message(tg_id, mess_text)
    except ChatNotFound:
        await users.update_active_status(tg_id, False)
        logger.error(f"Чата {tg_id} больше нет")
    except UserDeactivated:
        await users.update_active_status(tg_id, False)
        logger.error(f"Пользователя {tg_id} больше нет")
    except BotBlocked as e:
        await users.update_block_bot_status(tg_id, True)
        logger.error(f"Пользователь {tg_id} заблокировал бота: {e}")
    except Exception as e:
        logger.error(f"Отправка сообщения {tg_id} не удалась: {e}, {type(e)}")


@logger.catch
def balance_replenished(amount, current_language):
    message = {'ru': f'Баланс успешно пополнен на {amount}$.',
               'en': f'The balance was successfully replenished by {amount}$.'}
    return message[current_language]


async def notify_admins(text):
    admins_ = await admins.get_admins()
    tasks = [asyncio.create_task(bot_send_message(user, text)) for user in admins_]
    await asyncio.gather(*tasks)
