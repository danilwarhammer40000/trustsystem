from aiogram import Router, types
from aiogram.filters import Command

from services.user_service import get_all_users

router = Router()


@router.message(Command("stats"))
async def stats(message: types.Message):

    users = get_all_users()

    active = len([u for u in users if u.get("status") == "active"])
    inactive = len([u for u in users if u.get("status") != "active"])

    await message.answer(
        f"📊 Stats:\n"
        f"Active: {active}\n"
        f"Inactive: {inactive}\n"
        f"Total: {len(users)}"
    )
