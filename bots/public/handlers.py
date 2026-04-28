from aiogram import Router
from aiogram.types import Message
from core.tariffs import TARIFFS

router = Router()

@router.message()
async def menu(message: Message):
    text = "Тарифы:\n"

    for k, v in TARIFFS.items():
        text += f"{k} - {v['price']}$\n"

    await message.answer(text)
