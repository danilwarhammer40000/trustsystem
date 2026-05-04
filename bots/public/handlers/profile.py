from aiogram import Router, types
from services.public_user_service import get_user_by_tg

router = Router()


@router.message(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message):

    user = get_user_by_tg(message.from_user.id)

    if not user:
        return await message.answer("Нет профиля")

    status = "🟢 Active" if user["status"] == "active" else "🔴 Inactive"

    await message.answer(
        f"👤 Profile\n\n"
        f"User: {user['username']}\n"
        f"Status: {status}\n"
        f"Expires: {user.get('expires_at')}"
    )