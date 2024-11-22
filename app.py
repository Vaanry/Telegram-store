import asyncio
from datetime import datetime

from aiogram import executor
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import dp
import handlers
from middleware import check_balance
from utils import start_promo

scheduler = AsyncIOScheduler()


def set_scheduled_jobs(scheduler):
    logger.info("Добавляем задачу start_promo в планировщик")
    scheduler.add_job(start_promo, trigger='cron', hour=12, minute=30, day_of_week='thu', misfire_grace_time=3600 * 6)
    logger.info(f"Текущее время: {datetime.now()}")


async def start_sheduling():
    logger.info("Планировщик стартует")
    set_scheduled_jobs(scheduler)
    scheduler.start()
    logger.info("Планировщик запущен")


@logger.catch
async def on_startup(dp):
    pass


if __name__ == "__main__":
    try:

        print(
            """
                -----------------------------------
                Я новый бот!!!
                -----------------------------------
              """
        )
        loop = asyncio.get_event_loop()
        loop.create_task(check_balance(60))
        loop.create_task(start_sheduling())
        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)

        logger.info('Start')

    except (KeyboardInterrupt, SystemExit):
        logger.warning('Interrupt!')
