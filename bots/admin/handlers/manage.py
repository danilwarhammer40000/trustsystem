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
    set_expire,
    set_user_field
)

from services.control_plane import sync_all_users
from core.generator import generate_link
from config.settings import DOMAIN

router = Router()


# =========================
# HELPERS
# =========================

def format_expire(v):
    if not v:
        return "∞"
    try:
        return datetime.fromisoformat(v).strftime("%Y-%m-%d")
    except:
        return "∞"


def status(v):
    try:
        return "🟢" if datetime.fromisoformat(v or "") > datetime.utcnow() else "🔴"
    except:
        return "🔴"


def clean_link(l):
    return (l or "").split("\n")[0].split("To connect")[0].strip()


def card(user, link):
    return (
        f"👤 {user['username']}\n"
        f"🔑 {user['password']}\n"
        f"⏳ {format_expire(user.get('expires_at'))}\n\n"
        f"🔗 {clean_link(link)}"
    )


# =========================
# ADD USER
# =========================

@router.callback_query(F.data.startswith("days:"))
async def add(call: CallbackQuery):
    days = int(call.data.split(":")[1])
    tg_id = call.from_user.id

    user = create_user(tg_id)
    user = extend_user(tg_id, days)

    await asyncio.to_thread(sync_all_users)

    link = generate_link(user["username"], DOMAIN)

    await call.message.answer(card(user, link), reply_markup=main_menu)
    await call.answer()


# =========================
# EXTEND
# =========================

@router.callback_query(F.data.startswith("ext:"))
async def ext(call: CallbackQuery):
    _, username, days = call.data.split(":")

    user = next((u for u in get_all_users() if u["username"] == username), None)
    if not user:
        return await call.message.answer("not found")

    updated = extend_user(user["telegram_id"], int(days))

    await asyncio.to_thread(sync_all_users)

    await call.message.answer(
        f"{username}\n{format_expire(updated.get('expires_at'))}"
    )


# =========================
# DELETE
# =========================

@router.callback_query(F.data.startswith("del:"))
async def delete(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = next((u for u in get_all_users() if u["username"] == username), None)
    if user:
        delete_user(user["telegram_id"])

    await asyncio.to_thread(sync_all_users)

    await call.message.answer("deleted")