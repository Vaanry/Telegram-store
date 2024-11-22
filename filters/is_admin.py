from aiogram.types import Message
from aiogram.dispatcher.filters import BoundFilter

from crud import users


class IsAdmin(BoundFilter):
    async def check(self, message: Message):
        user = await users.get_user(message.from_user.id)

        return user.is_admin is True
