import os
import asyncio
import random
from datetime import datetime

import aioshutil
from loguru import logger
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from crud import promos, users
from .utils import bot_send_message


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)
promo_path = os.getenv('promo')

PROMO_DAY = 3


@logger.catch
def get_file():
    folder = os.path.join(promo_path, 'future_promo')
    files = os.listdir(folder)
    file = files[0]
    filename = os.path.join(folder, file)
    return filename


@logger.catch
async def is_promo_active(tg_id: int):
    promo = await promos.check_promo()
    now = datetime.now()
    if promo:
        status = promo.is_promo
        downloads = promo.downloads
        file = promo.file
        id = promo.id

    if promo is not None and now.weekday() == PROMO_DAY:

        if downloads < 10 and status == True:
            try:
                await promos.add_user_promo(tg_id, id)
                logger.info(f'User {tg_id} участвует в промо {id}')

                downloads += 1
                if downloads >= 10:
                    status = False
                    old_file = file
                    file = file.replace('future_promo', 'expired_promo')
                    await aioshutil.move(old_file, file)
                await promos.update_promo(id, status, downloads)
                return file
            except IntegrityError:
                return file
        else:
            return 'Expired'
    else:
        if promo is not None:
            if status == True:
                status = False
                old_file = file
                file = file.replace('future_promo', 'expired_promo')
                await aioshutil.move(old_file, file)
                await promos.update_promo(id, status, downloads)
        return 'No promo'


@logger.catch
async def start_promo():
    logger.info("start_promo запущена")
    random_minute = random.randint(0, 60)
    logger.info(f"Промоакция состоится через {random_minute} минут")
    await asyncio.sleep(random_minute * 60)
    file = get_file()
    users_ = await users.get_all_unblock_users()
    mess_text = '''Hi there! A new promo will start in the next few minutes! Hurry up to click /free at the right time!\n\nВсем привет! В ближайшие несколько минут стартует новая промо-акция! Успей нажать /free в нужное время!'''
    tasks = [asyncio.create_task(bot_send_message(user.tg_id, mess_text)) for user in users_]
    await asyncio.gather(*tasks)
    await promos.switch_promo_on(file)
