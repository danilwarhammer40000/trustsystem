from asyncio import to_thread
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

from core.generator import generate_link
from core.sync import safe_sync
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

        # FIX ∞
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

        # FIX ∞ always active
        if dt.year >= 2099:
            return "🟢"

        return "🟢" if dt > datetime.utcnow() else "🔴"
    except:
        return "🔴"


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
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
            ]
        ]
    )

    await msg.answer("Select password type:", reply_markup=kb)


# =========================
# PASSWORD SELECT
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
# DAYS BUTTONS
# =========================

async def show_days(target):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 days", callback_data="days:3"),
                InlineKeyboardButton(text="30 days", callback_data="days:30"),
            ],
            [
                InlineKeyboardButton(text="∞", callback_data="days:0"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
            ]
        ]
    )

    await target.answer("Select duration:", reply_markup=kb)


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

        expire = format_expire(user.get("expires_at"))
        link = generate_link(user["username"], DOMAIN)

        await call.message.answer(
            f"👤 {user['username']}\n"
            f"🔑 {user['password']}\n"
            f"⏳ {expire}\n\n"
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
            [
                InlineKeyboardButton(text="∞", callback_data=f"ext:{username}:0"),
            ],
            [
                InlineKeyboardButton(text="Manual", callback_data=f"manual:{username}")
            ],
            [
                InlineKeyboardButton(text="🔗 Get link", callback_data=f"link:{username}")
            ]
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

        await msg.answer("✅ Updated")

    except:
        await msg.answer("❌ Invalid date")

    await state.clear()


# =========================
# GET LINK (INLINE)
# =========================

@router.callback_query(F.data.startswith("link:"))
async def get_link(call: CallbackQuery):
    username = call.data.split(":")[1]

    link = generate_link(username, DOMAIN)

    if not link:
        await call.message.answer("❌ Error generating link")
    else:
        await call.message.answer(f"🔗 {link}")

    await call.answer()


# =========================
# GET LINK (MAIN MENU FIX)
# =========================

@router.message(F.text == "🔗 Get link")
async def get_link_menu(msg: Message):
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