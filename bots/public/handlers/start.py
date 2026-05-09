from aiogram import Router, types
from aiogram.filters import Command

router = Router()


def get_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🚀 Подключиться")],
            [types.KeyboardButton(text="🔄 Продлить")],
            [types.KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )


@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=get_menu())


# FIX: кнопка "назад" вызывает start
@router.message(lambda m: m.text == "/start")
async def start_text(message: types.Message):
    await start_cmd(message)