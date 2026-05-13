from aiogram import Router, types
from services.payment_service import create_payment
from services.public_user_service import get_or_create
from services.user_service import activate_trial
from services.vpn_card_builder import build_vpn_card
from core.sync import sync_all_users   # или full_sync

router = Router()

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

@router.message(lambda m: m.text in ["💳 30 дней", "💳 60 дней"])
async def buy(message: types.Message):
    tg_id = message.from_user.id
    plan = "30" if "30" in message.text else "60"
    get_or_create(tg_id)  # ensure user
    payment = create_payment(plan, tg_id)
    await message.answer(
        f"💳 Оплата: {payment['amount']} RUB\n\n"
        f"{payment['url']}\n\n"
        "⏳ После оплаты VPN придёт автоматически"
    )

@router.message(lambda m: m.text == "🎁 3 дня")
async def trial(message: types.Message):
    tg_id = message.from_user.id
    user = get_or_create(tg_id)
    try:
        activate_trial(tg_id)
        sync_all_users()
        card = build_vpn_card(user["username"])
        await message.answer(card.get("text", "Триал активирован!"))
    except ValueError:
        await message.answer("❌ Триал уже использован")