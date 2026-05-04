from aiogram import Router, types

router = Router()


@router.message(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message):
    await message.answer("👤 Профиль (заглушка)")