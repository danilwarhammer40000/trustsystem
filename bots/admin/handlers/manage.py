import asyncio
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bots.admin.states.user import AddUser
from bots.admin.keyboards.main import main_menu, cancel_kb

from services.user_service import (
    add_user,
    get_all_users,
    delete_user,
    get_user,
    update_user
)

from core.generator import generate_link
from core.service import safe_sync

router = Router()


# ---------------- CANCEL ----------------

@router.message(F.text == "❌ Cancel")
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Cancelled", reply_markup=main_menu)


# ---------------- ADD USER ----------------

@router.message(F.text == "➕ Add user")
async def add_user_start(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Enter username:", reply_markup=cancel_kb)


@router.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await state.set_state(AddUser.password)
    await msg.answer("Enter password:")


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

    expires_at = None if days == 0 else (
        datetime.utcnow() + timedelta(days=days)
    ).strftime("%Y-%m-%d")

    user = {
        "username": data["username"],
        "password": data["password"],
        "status": "active",
        "expires_at": expires_at
    }

    add_user(user)
    safe_sync()

    link = generate_link(user["username"])

    await msg.answer(
        f"👤 {user['username']}\n"
        f"🔑 {user['password']}\n"
        f"⏳ {expires_at or '∞'}\n\n"
        f"{link}",
        reply_markup=main_menu
    )

    await state.clear()


# ---------------- LIST USERS ----------------

@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users() or []

    if not users:
        await msg.answer("No users")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u["username"],
            callback_data=f"user:{u['username']}"
        )]
        for u in users
    ])

    await msg.answer("Users:", reply_markup=kb)


# ---------------- DELETE ----------------

@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: Message):
    users = get_all_users() or []

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u["username"],
            callback_data=f"del:{u['username']}"
        )]
        for u in users
    ])

    await msg.answer("Select:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)
    safe_sync()

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()


# ---------------- LINK ----------------

@router.message(F.text == "🔗 Get link")
async def link_menu(msg: Message):
    users = get_all_users() or []

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u["username"],
            callback_data=f"link:{u['username']}"
        )]
        for u in users
    ])

    await msg.answer("Select user:", reply_markup=kb)


@router.callback_query(F.data.startswith("link:"))
async def link_cb(call: CallbackQuery):
    username = call.data.split(":")[1]

    link = generate_link(username)

    await call.message.answer(f"🔗 {link}")
    await call.answer()


# ---------------- SYNC BUTTON ----------------

@router.message(F.text == "🔄 Sync users")
async def sync_btn(msg: Message):
    await msg.answer("🔄 Sync...")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, safe_sync)

    await msg.answer("✅ Done")


# ---------------- STATS BUTTON ----------------

@router.message(F.text == "📊 Stats")
async def stats_btn(msg: Message):
    users = get_all_users() or []

    await msg.answer(f"Users: {len(users)}")