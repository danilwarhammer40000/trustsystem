from aiogram import Router
from aiogram.types import Message

from bots.admin.keyboards.main import main_menu

router = Router()


@router.message()
async def start(msg: Message):
    if msg.text == "/start":
        await msg.answer("⚙️ Admin panel", reply_markup=main_menu)