from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start_cmd(message: types.Message):

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🚀 Подключиться")],
            [types.KeyboardButton(text="🔄 Продлить")],
            [types.KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🔐 VPN сервис\n\n"
        "Быстрое подключение\n"
        "Стабильная скорость\n"
        "Без логов\n\n"
        "💳 Тарифы:\n"
        "30 дней — 199 RUB\n"
        "60 дней — 349 RUB\n\n"
        "Выберите действие:",
        reply_markup=kb
    )