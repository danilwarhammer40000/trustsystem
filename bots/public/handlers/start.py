from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Подключить")],
        [KeyboardButton(text="👤 Профиль")]
    ],
    resize_keyboard=True
)


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 TrustSystem VPN\n\nВыберите действие:",
        reply_markup=kb
    )