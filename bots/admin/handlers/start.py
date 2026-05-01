from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bots.admin.keyboards.main import main_menu

router = Router()


@router.message(CommandStart())
async def start(msg: Message):
    await msg.answer("⚙️ Admin panel", reply_markup=main_menu)