from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Awaitable, Dict, Any

from config.settings import ADMIN_TG_ID


class AdminAccessMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ):

        user_id = getattr(event.from_user, "id", None)

        if user_id != ADMIN_TG_ID:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Access denied", show_alert=True)
            return

        return await handler(event, data)