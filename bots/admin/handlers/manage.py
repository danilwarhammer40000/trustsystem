import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import get_all_users, delete_user
from core.sync import full_sync                    # основной sync
from services.vpn_card_builder import build_vpn_card

router = Router()

# ====================== ADD USER ======================
@router.message(F.text == "➕ Add user")
async def add_user(message: Message):
    await message.answer("➕ Пока вручную создавай через List users или добавь пользователя в users.json")


# ====================== LIST USERS + GET LINK ======================
@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users() or []
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


@router.callback_query(F.data.startswith("user:"))
async def get_user_link(call: CallbackQuery):
    try:
        tg_id = int(call.data.split(":")[1])
        card = build_vpn_card(str(tg_id))
        await call.message.answer(card.get("text", "✅ Доступ"))
        await call.answer("✅ Отправлено")
    except Exception as e:
        await call.answer("Ошибка", show_alert=True)
        print(f"[LINK ERROR] {e}")


# ====================== DELETE ======================
@router.message(F.text == "❌ Delete user")
async def delete_menu(message: Message):
    users = get_all_users() or []
    if not users:
        return await message.answer("No users")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u.get("username", "unknown"),
            callback_data=f"del:{u.get('telegram_id')}"
        )]
        for u in users if u.get("telegram_id")
    ])

    await message.answer("Select user to delete:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_user_cb(call: CallbackQuery):
    try:
        tg_id = int(call.data.split(":")[1])
        if delete_user(tg_id):
            await asyncio.to_thread(full_sync)
            await call.message.answer(f"❌ Deleted user_{tg_id}")
            await call.answer("Удалено")
        else:
            await call.answer("Не найден", show_alert=True)
    except Exception as e:
        await call.answer("Ошибка", show_alert=True)
        print(f"[DELETE ERROR] {e}")


# ====================== SYNC ======================
@router.message(F.text == "🔄 Sync users")
async def sync_users(message: Message):
    try:
        await asyncio.to_thread(full_sync)
        await message.answer("✅ Синхронизация завершена")
    except Exception as e:
        await message.answer("❌ Ошибка синхронизации")
        print(f"[SYNC ERROR] {e}")


# ====================== STATS (дубликат) ======================
@router.message(F.text == "📊 Stats")
async def stats(message: Message):
    users = get_all_users() or []
    active = sum(1 for u in users if u.get("status") == "active")
    expired = len(users) - active
    await message.answer(
        f"📊 Stats:\n"
        f"Active: {active}\n"
        f"Expired: {expired}\n"
        f"Total: {len(users)}"
    )