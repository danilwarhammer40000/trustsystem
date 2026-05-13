import asyncio
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.user_service import (
    create_user,
    get_all_users,
    delete_user,
    extend_user,
    _update_user,
)

from services.control_plane import sync_all_users
from core.generator import generate_link
from config.settings import DOMAIN

router = Router()


# =========================
# LIST
# =========================

@router.message(F.text == "📋 List users")
async def list_users(msg: Message):
    users = get_all_users()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"user:{u['telegram_id']}"
                )
            ]
            for u in users
        ]
    )

    await msg.answer("Users:", reply_markup=kb)


# =========================
# EXTEND
# =========================

@router.callback_query(F.data.startswith("ext:"))
async def ext(call: CallbackQuery):
    _, tg_id, days = call.data.split(":")

    updated = extend_user(int(tg_id), int(days))

    await asyncio.to_thread(sync_all_users)

    await call.message.answer(
        f"{updated['username']}\n{updated.get('expires_at')}"
    )


# =========================
# GET LINK (FIXED)
# =========================

@router.callback_query(F.data.startswith("link:"))
async def link(call: CallbackQuery):
    tg_id = int(call.data.split(":")[1])

    user = next((u for u in get_all_users() if u["telegram_id"] == tg_id), None)
    if not user:
        return await call.message.answer("not found")

    link = generate_link(user["username"], DOMAIN)

    await call.message.answer(link)


# =========================
# DELETE
# =========================

@router.callback_query(F.data.startswith("del:"))
async def delete(call: CallbackQuery):
    tg_id = int(call.data.split(":")[1])

    delete_user(tg_id)

    await asyncio.to_thread(sync_all_users)

    await call.message.answer("deleted")