from aiogram import Router, types

router = Router()


@router.message(lambda m: m.text == "/pay")
async def pay(message: types.Message):
    await message.answer(
        "💳 Payment system not implemented yet"
    )
