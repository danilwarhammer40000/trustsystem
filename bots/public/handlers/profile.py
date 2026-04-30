from aiogram import Router

router = Router()


@router.message()
async def profile_stub(message):
    await message.answer("Profile module is not implemented yet.")
