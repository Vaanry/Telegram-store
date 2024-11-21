import asyncio
from loguru import logger
from utils import crypto_cloud_balance_updater


@logger.catch
async def check_balance(timeout: int):
    while True:
        try:
            await crypto_cloud_balance_updater()
        except Exception as e:
            logger.error(f'Ошибка CryptoCloud: {e}')
        await asyncio.sleep(timeout)
