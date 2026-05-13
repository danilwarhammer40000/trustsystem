from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from services.public_user_service import get_or_create
from services.user_service import activate_trial
from services.payment_service import create_payment
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

router = Router()

main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🚀 Подключиться")]],
    resize_keyboard=True
)

tariff_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 3 дня")],
        [KeyboardButton(text="💳 30 дней")],
        [KeyboardButton(text="💳 60 дней")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


@router.message(F.text == "/start")
async def start(msg: types.Message):
    await msg.answer(
        "Добро пожаловать в TrustTunnel VPN\n\n"
        "Нажмите кнопку ниже для подключения:",
        reply_markup=main_kb
    )


@router.message(F.text == "🚀 Подключиться")
async def connect(msg: types.Message):
    await msg.answer("Выберите вариант:", reply_markup=tariff_kb)


@router.message(F.text == "🎁 3 дня")
async def trial_handler(msg: types.Message):
    user = get_or_create(msg.from_user.id)
    try:
        activate_trial(msg.from_user.id)
        full_sync()
        card = build_vpn_card(str(msg.from_user.id))
        await msg.answer(card.get("text", "✅ Триал активирован!"))
    except ValueError:
        await msg.answer("❌ Вы уже использовали триал.")
    except Exception as e:
        await msg.answer("❌ Ошибка активации триала.")
        print(f"Trial error: {e}")


@router.message(F.text.in_({"💳 30 дней", "💳 60 дней"}))
async def payment_handler(msg: types.Message):
    days = 30 if "30" in msg.text else 60
    get_or_create(msg.from_user.id)

    payment = create_payment(str(days), msg.from_user.id)

    await msg.answer(
        f"💳 Оплата за {days} дней: {payment.get('amount', 0)} RUB\n\n"
        f"Ссылка на оплату:\n{payment.get('url')}\n\n"
        "После успешной оплаты доступ придёт автоматически.",
        disable_web_page_preview=True
    )


@router.message(F.text == "⬅️ Назад")
async def back(msg: types.Message):
    await msg.answer("Возвращаемся в главное меню", reply_markup=main_kb)