@router.message(Command("start"))
async def start_cmd(message: types.Message):

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💳 30 дней")],
            [types.KeyboardButton(text="💳 60 дней")],
            [types.KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "VPN доступ\n\nВыберите тариф:",
        reply_markup=kb
    )