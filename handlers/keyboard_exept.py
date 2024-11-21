from utils import get_text

from .start import cmd_start, switch_language, about, user_help
from .payment import payment
from .catalog import catalog


async def submit_cheker(message, state, current_language):
    await state.finish()
    if message.text in ("🗂Каталог", "🗂Catalog", "💰Пополнить", "💰Top up", "🇷🇺RU/EN🇺🇸", "/start", "/help", 'ℹ️О нас', 'ℹ️About us'):
        if message.text in ("🗂Каталог", "🗂Catalog"):
            await catalog(message, state)
        if message.text in ("💰Пополнить", "💰Top up"):
            await payment(message, state)
        elif message.text == "🇷🇺RU/EN🇺🇸":
            await switch_language(message)
        elif message.text == "/start":
            await cmd_start(message)
        elif message.text in ('ℹ️О нас', 'ℹ️About us'):
            await about(message)
        elif message.text == "/help":
            await user_help(message)
    else:
        await message.answer(get_text("incorrect input", current_language))
        return
