import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user, create_user
from services.control_plane import sync_all_users
from core.generator import generate_link
from config.settings import DOMAIN
from services.vpn_card_builder import build_vpn_card

router = Router()

# ====================== LIST USERS ======================
@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users()
    if not users:
        return await msg.answer("No users")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{u.get('username')} | {u.get('status')}",
            callback_data=f"user:{u.get('telegram_id')}"
        )]
        for u in users if u.get("telegram_id")
    ])

    await msg.answer("📋 Users:", reply_markup=kb)


# ====================== GET LINK ======================
@router.callback_query(F.data.startswith("user:"))
async def get_link(call: CallbackQuery):
    try:
        tg_id = int(call.data.split(":")[1])
        card = build_vpn_card(str(tg_id))
        await call.message.answer(card.get("text", "Доступ выдан"))
        await call.answer("✅ Link sent")
    except Exception as e:
        await call.answer("Ошибка", show_alert=True)
        print(f"[GET LINK ERROR] {e}")


# ====================== DELETE MENU ======================
@router.message(F.text == "❌ Delete user")
async def delete_menu(message: Message):
    users = get_all_users()
    if not users:
        return await message.answer("No users")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u.get("username"),
            callback_data=f"del:{u.get('telegram_id')}"
        )]
        for u in users if u.get("telegram_id")
    ])

    await message.answer("Select user to delete:", reply_markup=kb)


# ====================== DELETE ACTION ======================
@router.callback_query(F.data.startswith("del:"))
async def delete_user_cb(call: CallbackQuery):
    try:
        tg_id = int(call.data.split(":")[1])
        username = f"user_{tg_id}"
        
        if delete_user(tg_id):
            await asyncio.to_thread(sync_all_users)
            await call.message.answer(f"❌ Deleted: {username}")
            await call.answer("Пользователь удалён")
        else:
            await call.answer("Не удалось удалить", show_alert=True)
    except Exception as e:
        await call.answer("Ошибка удаления", show_alert=True)
        print(f"[DELETE ERROR] {e}")


# ====================== ADD USER ======================
@router.message(F.text == "➕ Add user")
async def add_user(message: Message):
    # Можно сделать запрос TG ID, но для простоты — заглушка
    await message.answer("Введи Telegram ID пользователя:")
    # В будущем можно добавить FSM для ввода