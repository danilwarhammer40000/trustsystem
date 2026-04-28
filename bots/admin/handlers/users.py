from aiogram import Router, types
from aiogram.filters import Command

from services.user_service import get_all_users, delete_user

router = Router()


@router.message(Command("users"))
async def list_users(message: types.Message):

    users = get_all_users()

    if not users:
        await message.answer("No users")
        return

    text = "\n".join(
        f"{u['username']} | {u.get('status')} | {u.get('expires_at')}"
        for u in users
    )

    await message.answer(text)


@router.message(Command("delete"))
async def delete(message: types.Message):

    args = message.text.split()

    if len(args) < 2:
        await message.answer("Usage: /delete username")
        return

    username = args[1]

    delete_user(username)

    await message.answer(f"Deleted: {username}")
