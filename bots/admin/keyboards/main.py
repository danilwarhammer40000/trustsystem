from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Add user")],
        [KeyboardButton(text="📋 List users")],
        [KeyboardButton(text="❌ Delete user")],
        [KeyboardButton(text="🔗 Get link")],
        [KeyboardButton(text="🔄 Sync users")],
        [KeyboardButton(text="📊 Stats")]
    ],
    resize_keyboard=True
)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Cancel")]
    ],
    resize_keyboard=True
)