from aiogram import Router, F, types

from services.user_service import get_all_users, delete_user

router = Router()


# =========================
# LIST USERS
# =========================

@router.message(F.text == "📋 List users")
async def list_users(message: types.Message):

    users = get_all_users() or []

    if not users:
        await message.answer("No users")
        return

    text = "\n".join(
        f"{u['username']} | {u.get('status')} | {u.get('expires_at')}"
        for u in users
    )

    await message.answer(text)


# =========================
# DELETE MENU
# =========================

@router.message(F.text == "❌ Delete user")
async def delete_menu(message: types.Message):

    users = get_all_users() or []

    if not users:
        await message.answer("No users")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=u["username"], callback_data=f"del:{u['username']}")]
            for u in users
        ]
    )

    await message.answer("Select user to delete:", reply_markup=kb)


# =========================
# DELETE ACTION
# =========================

@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call):

    username = call.data.split(":")[1]

    delete_user(username)

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()