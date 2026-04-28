from aiogram import Router
from aiogram.types import Message
from core.credentials import create_credential

router = Router()

@router.message()
async def create_user(message: Message):
    # временно: /create user pass 30
    parts = message.text.split()

    if parts[0] == "/create":
        _, username, password, days = parts

        create_credential(
            user_id=message.from_user.id,
            username=username,
            password=password,
            days=int(days)
        )

        await message.answer("Создано")
