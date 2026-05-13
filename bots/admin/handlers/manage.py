import asyncio
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import (
    create_user,
    get_all_users,
    delete_user,
    extend_user,
    get_user_by_username,
    set_expire
)

from services.control_plane import sync_all_users
from core.generator import generate_link
from config.settings import DOMAIN

router = Router()


def format_expire(v):
    if not v:
        return "∞"
    try:
        return datetime.fromisoformat(v).strftime("%Y-%m-%d")
    except:
        return "∞"


def clean(l):
    return (l or "").split("\n")[0]


def card(user, link):
    return f"👤 {user['username']}\n🔑 {user['password']}\n⏳ {format_expire(user.get('expires_at'))}\n🔗 {clean(link)}"


@router.callback_query(F.data.startswith("days:"))
async def add(call: CallbackQuery):
    days = int(call.data.split(":")[1])
    tg_id = call.from_user.id

    user = create_user(tg_id)
    user = extend_user(tg_id, days)

    await asyncio.to_thread(sync_all_users)

    link = generate_link(user["username"], DOMAIN)

    await call.message.answer(card(user, link))
    await call.answer()


@router.callback_query(F.data.startswith("ext:"))
async def ext(call: CallbackQuery):
    _, username, days = call.data.split(":")

    user = get_user_by_username(username)
    if not user:
        return await call.message.answer("not found")

    updated = extend_user(user["telegram_id"], int(days))

    await asyncio.to_thread(sync_all_users)

    await call.message.answer(f"{username}\n{format_expire(updated.get('expires_at'))}")


@router.callback_query(F.data.startswith("del:"))
async def delete(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = get_user_by_username(username)
    if user:
        delete_user(user["telegram_id"])

    await asyncio.to_thread(sync_all_users)
    await call.message.answer("deleted")