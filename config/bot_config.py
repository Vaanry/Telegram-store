import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("token_bot")
CRYPTO_TOKEN = os.getenv('token_pay')
CLOUD_TOKEN = os.getenv('cloud_token')
SHOP_ID = os.getenv('shop_id')
MANAGER = int(os.getenv('manager'))

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)
