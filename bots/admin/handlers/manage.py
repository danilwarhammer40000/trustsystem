import asyncio
from asyncio import to_thread
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
# FSM (MANUAL EXTEND)
# =========================

class ExtendManual(StatesGroup):
    username = State()
    date = State()


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
        # ❗ tg_id УБРАН
        user = create_user(
            username=data["username"]
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
# LIST USERS → EXTEND FLOW
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
                    callback_data=f"extend:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Select user:", reply_markup=kb)


# =========================
# EXTEND MENU
# =========================

@router.callback_query(F.data.startswith("extend:"))
async def extend_menu(call: CallbackQuery):
    username = call.data.split(":")[1]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 days", callback_data=f"ext:{username}:3"),
                InlineKeyboardButton(text="30 days", callback_data=f"ext:{username}:30"),
            ],
            [
                InlineKeyboardButton(text="∞", callback_data=f"ext:{username}:0"),
            ],
            [
                InlineKeyboardButton(text="Manual", callback_data=f"ext_manual:{username}")
            ]
        ]
    )

    await call.message.answer(f"Extend user: {username}", reply_markup=kb)
    await call.answer()


# =========================
# APPLY EXTEND
# =========================

@router.callback_query(F.data.startswith("ext:"))
async def extend_apply(call: CallbackQuery):
    _, username, days = call.data.split(":")
    days = int(days)

    try:
        extend_user(username, days)

        await call.message.answer(
            f"✅ Extended {username} by {days if days > 0 else '∞'} days"
        )

    except Exception as e:
        await call.message.answer(f"❌ Error: {str(e)}")

    await call.answer()


# =========================
# MANUAL EXTEND (FSM)
# =========================

@router.callback_query(F.data.startswith("ext_manual