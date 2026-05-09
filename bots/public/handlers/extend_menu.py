from aiogram import Router, types
from services.public_user_service import get_by_tg
from services.payment_service import create_payment

router = Router()


@router.message(lambda m: m.text == "🔄 Продлить")
async def extend_menu(message: types.Message):

    user = get_by_tg(message.from_user.id)

    if not user:
        return await message.answer("Сначала подключитесь")

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💳 30 дней")],
            [types.KeyboardButton(text="💳 60 дней")],
            [types.KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите продление:", reply_markup=kb)