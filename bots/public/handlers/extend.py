from aiogram import Router, types

from services.user_service import extend_user

router = Router()


@router.message(lambda m: m.text and m.text.startswith("/extend"))
async def extend(message: types.Message):

    parts = message.text.split()

    if len(parts) < 3:
        await message.answer("Usage: /extend username days")
        return

    username = parts[1]
    days = int(parts[2])

    user = extend_user(username, days)

    await message.answer(
        f"✅ Extended\n"
        f"{username}\n"
        f"expires: {user['expires_at']}"
    )
