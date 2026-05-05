from aiogram import Router, types
from services.public_user_service import get_by_tg

router = Router()

@router.message(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message):

    user = get_by_tg(message.from_user.id)

    if not user:
        return await message.answer("Нет активного доступа")

    status = "🟢 Активен" if user["status"] == "active" else "🔴 Неактивен"

    await message.answer(
        f"👤 Профиль\n\n"
        f"Статус: {status}\n"
        f"До: {user.get('expires_at')}"
    )