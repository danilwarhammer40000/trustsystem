from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Welcome to TrustSystem\n"
        "Use /connect to create access"
    )
