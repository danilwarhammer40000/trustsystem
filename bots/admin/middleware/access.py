from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from config.settings import ADMIN_TG_ID


class AdminAccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):

        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id != ADMIN_TG_ID:
            if isinstance(event, Message):
                await event.answer("⛔ Access denied")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Access denied", show_alert=True)
            return

        return await handler(event, data)
