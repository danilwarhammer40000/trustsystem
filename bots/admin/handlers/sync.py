from aiogram import Router, types
from aiogram.filters import Command

from core.sync import full_sync

router = Router()


@router.message(Command("sync"))
async def sync_cmd(message: types.Message):

    try:
        full_sync()
        await message.answer("✅ Sync completed")
    except Exception as e:
        await message.answer(f"❌ Sync error: {str(e)}")
