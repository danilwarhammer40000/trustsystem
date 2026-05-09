from aiogram import Router, F, types

from services.user_service import get_all_users

router = Router()


@router.message(F.text == "📊 Stats")
async def stats(message: types.Message):

    users = get_all_users() or []

    active = sum(1 for u in users if u.get("status") == "active")
    inactive = sum(1 for u in users if u.get("status") != "active")

    await message.answer(
        "📊 Stats:\n"
        f"Active: {active}\n"
        f"Inactive: {inactive}\n"
        f"Total: {len(users)}"
    )