from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user

router = Router()


# =========================
# LIST USERS (FIXED UI)
# =========================

@router.message(F.text == "📋 List users")
async def list_users(message: types.Message):

    users = get_all_users() or []

    if not users:
        await message.answer("No users")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{u.get('username')} | {u.get('status')} | {u.get('expires_at')}",
                    callback_data=f"user:{u.get('username')}"
                )
            ]
            for u in users if u.get("username")
        ]
    )

    await message.answer("📋 Users:", reply_markup=kb)


# =========================
# DELETE MENU
# =========================

@router.message(F.text == "❌ Delete user")
async def delete_menu(message: types.Message):

    users = get_all_users() or []

    if not users:
        await message.answer("No users")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=u.get("username"),
                    callback_data=f"del:{u.get('username')}"
                )
            ]
            for u in users if u.get("username")
        ]
    )

    await message.answer("Select user to delete:", reply_markup=kb)


# =========================
# DELETE ACTION (FIXED)
# =========================

@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: types.CallbackQuery):

    username = call.data.split(":")[1]

    if not username:
        await call.answer("Invalid user", show_alert=True)
        return

    result = delete_user(username)

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()