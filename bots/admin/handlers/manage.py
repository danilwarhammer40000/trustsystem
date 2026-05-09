import asyncio
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bots.admin.states.user import AddUser, ManualDate
from bots.admin.keyboards.main import main_menu

from services.user_service import (
    create_user,
    get_all_users,
    delete_user,
    extend_user,
    set_expire
)

from services.control_plane import sync_all_users

from core.generator import generate_link
from config.settings import DOMAIN


router = Router()


# =========================
# HELPERS
# =========================

def format_expire(date_str):
    if not date_str:
        return "∞"

    try:
        dt = datetime.fromisoformat(date_str)

        if dt.year >= 2099:
            return "∞"

        return dt.strftime("%y-%m-%d")
    except:
        return "?"


def status_emoji(date_str):
    if not date_str:
        return "🟢"

    try:
        dt = datetime.fromisoformat(date_str)

        if dt.year >= 2099:
            return "🟢"

        return "🟢" if dt > datetime.utcnow() else "🔴"
    except:
        return "🔴"


# =========================
# LINK CLEANER
# =========================

def clean_link(link: str) -> str:
    if not link:
        return ""

    link = link.strip()

    if "To connect on mobile" in link:
        link = link.split("To connect on mobile")[0].strip()

    if "\n" in link:
        link = link.split("\n")[0].strip()

    return link


def build_user_card(user, link):
    expire = format_expire(user.get("expires_at"))
    link = clean_link(link)

    if "tt://" in link:
        qr_token = link.replace("tt://?", "")
    else:
        qr_token = link

    return (
        f"👤 {user['username']}\n"
        f"🔑 {user['password']}\n"
        f"⏳ {expire}\n\n"
        f"🔗 {link}\n\n"
        f"To connect on mobile, scan QR:\n"
        f"https://trusttunnel.org/qr.html#tt={qr_token}"
    )


def cancel_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )


# =========================
# GLOBAL CANCEL
# =========================

@router.callback_query(F.data == "cancel")
async def cancel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Cancelled", reply_markup=main_menu)
    await call.answer()


# =========================
# ADD USER
# =========================

@router.message(F.text == "➕ Add user")
async def add_user_start(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Enter username:", reply_markup=cancel_inline())


@router.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Manual", callback_data="pass:manual"),
                InlineKeyboardButton(text="⚙️ Auto", callback_data="pass:auto"),
            ],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )

    await msg.answer("Select password type:", reply_markup=kb)


# =========================
# PASSWORD
# =========================

@router.callback_query(F.data.startswith("pass:"))
async def password_select(call: CallbackQuery, state: FSMContext):
    mode = call.data.split(":")[1]

    if mode == "manual":
        await state.set_state(AddUser.password)
        await call.message.answer("Enter password:")
    else:
        await state.update_data(password="-")
        await show_days(call.message)

    await call.answer()


@router.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text.strip())
    await show_days(msg)


# =========================
# DAYS
# =========================

async def show_days(target):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 days", callback_data="days:3"),
                InlineKeyboardButton(text="30 days", callback_data="days:30"),
            ],
            [InlineKeyboardButton(text="∞", callback_data="days:0")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )

    await target.answer("Select duration:", reply_markup=kb)


# =========================
# CREATE USER
# =========================

@router.callback_query(F.data.startswith("days:"))
async def add_finish(call: CallbackQuery, state: FSMContext):
    days = int(call.data.split(":")[1])
    data = await state.get_data()

    try:
        user = create_user(
            username=data["username"],
            password=data.get("password")
        )

        user = extend_user(user["username"], days)

        # ✅ НОВАЯ ЛОГИКА
        await asyncio.to_thread(sync_all_users)

        link = clean_link(generate_link(user["username"], DOMAIN))

        await call.message.answer(
            build_user_card(user, link),
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
                    text=f"{status_emoji(u.get('expires_at'))} {u['username']} | {format_expire(u.get('expires_at'))}",
                    callback_data=f"user:{u['username']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Users:", reply_markup=kb)


# =========================
# USER MENU
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
            [InlineKeyboardButton(text="∞", callback_data=f"ext:{username}:0")],
            [InlineKeyboardButton(text="Manual", callback_data=f"manual:{username}")],
            [InlineKeyboardButton(text="🔗 Get link", callback_data=f"link:{username}")]
        ]
    )

    await call.message.answer(username, reply_markup=kb)
    await call.answer()


# =========================
# EXTEND
# =========================

@router.callback_query(F.data.startswith("ext:"))
async def extend_apply(call: CallbackQuery):
    _, username, days = call.data.split(":")
    user = extend_user(username, int(days))

    await asyncio.to_thread(sync_all_users)

    expire = format_expire(user.get("expires_at"))

    await call.message.answer(f"✅ {username}\n⏳ {expire}")
    await call.answer()


# =========================
# MANUAL DATE
# =========================

@router.callback_query(F.data.startswith("manual:"))
async def manual_start(call: CallbackQuery, state: FSMContext):
    username = call.data.split(":")[1]

    await state.set_state(ManualDate.date)
    await state.update_data(username=username)

    await call.message.answer("Enter date YYYY-MM-DD:", reply_markup=cancel_inline())
    await call.answer()


@router.message(ManualDate.date)
async def manual_apply(msg: Message, state: FSMContext):
    data = await state.get_data()

    try:
        dt = datetime.fromisoformat(msg.text.strip())
        set_expire(data["username"], dt)

        await asyncio.to_thread(sync_all_users)

        await msg.answer("✅ Updated")

    except:
        await msg.answer("❌ Invalid date")

    await state.clear()


# =========================
# GET LINK
# =========================

@router.callback_query(F.data.startswith("link:"))
async def get_link(call: CallbackQuery):
    username = call.data.split(":")[1]

    users = get_all_users() or []
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        await call.message.answer("❌ User not found")
        await call.answer()
        return

    link = clean_link(generate_link(username, DOMAIN))

    await call.message.answer(
        build_user_card(user, link),
        reply_markup=main_menu
    )

    await call.answer()


# =========================
# DELETE
# =========================

@router.callback_query(F.data.startswith("del:"))
async def delete_cb(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)

    await asyncio.to_thread(sync_all_users)

    await call.message.answer("❌ Deleted")
    await call.answer()


# =========================
# SYNC
# =========================

@router.message(F.text == "🔄 Sync users")
async def sync_btn(msg: Message):
    await msg.answer("Sync...")
    await asyncio.to_thread(sync_all_users)
    await msg.answer("✅ Done")