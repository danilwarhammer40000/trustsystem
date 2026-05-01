from asyncio import to_thread
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bots.admin.states.user import AddUser, ManualDate
from bots.admin.keyboards.main import main_menu, cancel_kb

from services.user_service import (
    create_user,
    get_all_users,
    delete_user,
    extend_user,
    set_expire
)

from core.generator import generate_link
from core.sync import safe_sync
from config.settings import DOMAIN


router = Router()


# =========================
# ADD USER
# =========================

@router.message(F.text == "➕ Add user")
async def add_user_start(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Enter username:", reply_markup=cancel_kb)


@router.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await state.set_state(AddUser.password)
    await msg.answer("Enter password (or '-' to auto):")


@router.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text.strip())

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 days", callback_data="days:3"),
                InlineKeyboardButton(text="30 days", callback_data="days:30"),
            ],
            [
                InlineKeyboardButton(text="∞", callback_data="days:0"),
            ]
        ]
    )

    await msg.answer("Select duration:", reply_markup=kb)


@router.callback_query(F.data.startswith("days:"))
async def add_finish(call: CallbackQuery, state: FSMContext):
    days = int(call.data.split(":")[1])
    data = await state.get_data()

    try:
        user = create_user(
            username=data["username"],
            password=data["password"]
        )

        extend_user(user["username"], days)

        link = generate_link(user["username"], DOMAIN)

        await call.message.answer(
            f"👤 {user['username']}\n"
            f"🔑 {user['password']}\n"
            f"⏳ {days if days else '∞'}\n\n"
            f"🔗 {link}",
            reply_markup=main_menu
        )

    except Exception as e:
        await call.message.answer(f"❌ {str(e)}")

    await state.clear()
    await call.answer()


# =========================
# LIST USERS
# =========================

@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users() or []

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"user:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Users:", reply_markup=kb)


# =========================
# EXTEND MENU
# =========================

@router.callback_query(F.data.startswith("user:"))
async def user_menu(call: CallbackQuery):
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
                InlineKeyboardButton(text="Manual", callback_data=f"manual:{username}")
            ]
        ]
    )

    await call.message.answer(f"{username}", reply_markup=kb)
    await call.answer()


# =========================
# EXTEND APPLY
# =========================

@router.callback_query(F.data.startswith("ext:"))
async def extend_apply(call: CallbackQuery):
    _, username, days = call.data.split(":")
    extend_user(username, int(days))

    await call.message.answer("✅ Done")
    await call.answer()


# =========================
# MANUAL DATE
# =========================

@router.callback_query(F.data.startswith("manual:"))
async def manual_start(call: CallbackQuery, state: FSMContext):
    username = call.data.split(":")[1]

    await state.set_state(ManualDate.date)
    await state.update_data(username=username)

    await call.message.answer("Enter date YYYY-MM-DD:")
    await call.answer()


@router.message(ManualDate.date)
async def manual_apply(msg: Message, state: FSMContext):
    data = await state.get_data()

    try:
        dt = datetime.fromisoformat(msg.text.strip())
        set_expire(data["username"], dt)

        await msg.answer("✅ Updated")

    except Exception:
        await msg.answer("❌ Invalid date")

    await state.clear()


# =========================
# DELETE
# =========================

@router.message(F.text == "❌ Delete user")
async def delete_menu(msg: Message):
    users = get_all_users()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=u["username"], callback_data=f"del:{u['username']}")]
            for u in users
        ]
    )

    await msg.answer("Select:", reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: CallbackQuery):
    username = call.data.split(":")[1]
    delete_user(username)

    await call.message.answer("❌ Deleted")
    await call.answer()


# =========================
# SYNC
# =========================

@router.message(F.text == "🔄 Sync users")
async def sync_btn(msg: Message):
    await msg.answer("Sync...")
    await to_thread(safe_sync)
    await msg.answer("✅ Done")