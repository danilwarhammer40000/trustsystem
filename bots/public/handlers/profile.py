from aiogram import Router, types, F

from services.user_service import load_users

router = Router()


@router.message(F.text == "👤 Профиль")
async def profile(message: types.Message):

    tg_id = message.from_user.id

    users = load_users()

    user = next((u for u in users if u.get("telegram_id") == tg_id), None)

    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    await message.answer(
    f"👤 {user['username']}\n"
    f"📦 {user['plan']}\n"
    f"📊 {user['status']}\n"
    f"⏳ {user['expires_at']}\n\n"
    f"Для продления нажмите 🚀 Подключить"
)