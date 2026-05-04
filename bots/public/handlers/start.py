from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🚀 Подключить")],
            [types.KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )

    await message.answer("👋 TrustSystem VPN\n\nВыберите действие:", reply_markup=kb)