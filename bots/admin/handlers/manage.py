import asyncio
from asyncio import to_thread

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bots.admin.states.user import AddUser
from bots.admin.keyboards.main import main_menu, cancel_kb

from services.user_service import (
    create_user,
    get_all_users,
    delete_user,
    get_user,
    extend_user
)

from core.generator import generate_link
from core.sync import safe_sync
from config.settings import DOMAIN


router = Router()


# =========================
# CANCEL
# =========================

@router.message(F.text == "❌ Cancel")
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Cancelled", reply_markup=main_menu)


# =========================
# ADD USER (FSM)
# =========================

@router.message(F.text == "➕ Add user")
async def add_user_start(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Enter username:", reply_markup=cancel_kb)


@router.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await state.set_state(AddUser.password)
    await msg.answer("Enter password (or '-' to auto-generate):")


@router.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text.strip())
    await state.set_state(AddUser.days)
    await msg.answer("Days (3 / 30 / 0):")


@router.message(AddUser.days)
async def add_days(msg: Message, state: FSMContext):
    data = await state.get_data()

    try:
        days = int(msg.text.strip())
    except:
        await msg.answer("Use 3 / 30 / 0")
        return

    try:
        user = create_user(
            username=data["username"],
            tg_id=msg.from_user.id
        )

        if days > 0:
            extend_user(user["username"], days)

    except Exception as e:
        await msg.answer(f"❌ Error: {str(e)}", reply_markup=main_menu)
        await state.clear()
        return

    link = generate_link(user["username"], DOMAIN)

    await msg.answer(
        f"👤 Username: {user['username']}\n"
        f"🔑 Password: {user['password']}\n"
        f"⏳ Days: {days if days > 0 else '∞'}\n\n"
        f"🔗 {link}",
        reply_markup=main_menu
    )

    await state.clear()


# =========================
# LIST USERS
# =========================

@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users() or []

    if not users:
        await msg.answer("No users")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{u['username']} ({u.get('expires_at') or '∞'})",
                    callback_data=f"user:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Users:", reply_markup=kb)


# =========================
# USER INFO (ВАЖНО — у тебя этого не было)
# =========================

@router.callback_query(F.data.startswith("user:"))
async def user_info(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = get_user(username)

    if not user:
        await call.answer("User not found", show_alert=True)
        return

    link = generate_link(username, DOMAIN)

    await call.message.answer(
        f"👤 {username}\n"
        f"🔑 {user.get('password')}\n"
        f"⏳ {user.get('expires_at') or '∞'}\n\n"
        f"🔗 {link}"
    )

    await call.answer()


# =========================
# DELETE
# =========================

@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: Message):
    users = get_all_users() or []

    if not users:
        await msg.answer("No users")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"del:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Select user:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()


# =========================
# GET LINK
# =========================

@router.message(F.text == "🔗 Get link")
async def link_menu(msg: Message):
    users = get_all_users() or []

    if not users:
        await msg.answer("No users")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"link:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Select user:", reply_markup=kb)


@router.callback_query(F.data.startswith("link:"))
async def link_cb(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = get_user(username)
    link = generate_link(username, DOMAIN)

    await call.message.answer(
        f"👤 {username}\n"
        f"🔑 {user.get('password')}\n"
        f"⏳ {user.get('expires_at') or '∞'}\n\n"
        f"🔗 {link}"
    )

    await call.answer()


# =========================
# SYNC
# =========================

@router.message(F.text == "🔄 Sync users")
async def sync_btn(msg: Message):
    await msg.answer("🔄 Sync...")

    await to_thread(safe_sync)

    await msg.answer("✅ Sync done")


# =========================
# STATS
# =========================

@router.message(F.text == "📊 Stats")
async def stats_btn(msg: Message):
    users = get_all_users() or []

    active = len([u for u in users if u.get("status") == "active"])

    await msg.answer(
        f"📊 Stats:\n"
        f"Active: {active}\n"
        f"Total: {len(users)}"
    )