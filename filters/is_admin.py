from aiogram.types import Message
from aiogram.dispatcher.filters import BoundFilter

from crud import db_api


class IsAdmin(BoundFilter):
    async def check(self, message: Message):
        user = await db_api.get_user(message.from_user.id)

        return user.is_admin is True
