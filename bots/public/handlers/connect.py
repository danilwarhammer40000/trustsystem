from aiogram import Router, types

from services.payment_service import create_payment
from services.public_user_service import get_or_create
from services.user_service import activate_trial
from services.control_plane import sync_all_users
from services.vpn_card_builder import build_vpn_card

router = Router()


# =========================
# CONNECT MENU
# =========================

@router.message(lambda m: m.text == "🚀 Подключиться")
async def connect(message: types.Message):

    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🎁 3 дня")],
            [types.KeyboardButton(text="💳 30 дней")],
            [types.KeyboardButton(text="💳 60 дней")],
            [types.KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите тариф:", reply_markup=kb)


# =========================
# BUY
# =========================

@router.message(lambda m: m.text in ["💳 30 дней", "💳 60 дней"])
async def buy(message: types.Message):

    tg_id = message.from_user.id
    plan = "30" if "30" in message.text else "60"

    user = get_or_create(tg_id)

    payment = create_payment(plan, tg_id)

    await message.answer(
        f"💳 Оплата: {payment['amount']} RUB\n\n"
        f"{payment['url']}\n\n"
        "⏳ После оплаты VPN придёт автоматически"
    )


# =========================
# TRIAL (FIX)
# =========================

@router.message(lambda m: m.text == "🎁 3 дня")
async def trial(message: types.Message):

    tg_id = message.from_user.id
    user = get_or_create(tg_id)

    try:
        activate_trial(user["username"])
    except ValueError:
        return await message.answer("❌ Триал уже использован")

    # FIX: синк + выдача
    sync_all_users()

    card = build_vpn_card(user["username"])

    await message.answer(card["text"])


# =========================
# BACK (FIX)
# =========================

@router.message(lambda m: m.text == "⬅️ Назад")
async def back(message: types.Message):
    await message.answer("/start")