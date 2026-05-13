from aiogram import Router, types
from services.payment_service import create_payment
from services.public_user_service import get_or_create
from services.user_service import activate_trial
from core.sync import full_sync
from services.vpn_card_builder import build_vpn_card

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


@router.message(lambda m: m.text.startswith("💳"))
async def buy(message: types.Message):
    tg_id = message.from_user.id
    days = 30 if "30" in message.text else 60
    get_or_create(tg_id)

    payment = create_payment(str(days), tg_id)

    await message.answer(
        f"💳 Оплата: {payment.get('amount', 0)} RUB\n\n"
        f"{payment.get('url', 'Ошибка создания ссылки')}\n\n"
        "⏳ После оплаты доступ придёт автоматически."
    )


@router.message(lambda m: m.text == "🎁 3 дня")
async def trial(message: types.Message):
    tg_id = message.from_user.id
    try:
        user = activate_trial(tg_id)
        full_sync()
        card = build_vpn_card(str(tg_id))
        await message.answer(card.get("text", "✅ Триал активирован!"))
    except ValueError:
        await message.answer("❌ Триал уже использован")
    except Exception as e:
        await message.answer("❌ Ошибка активации")
        print(f"[TRIAL ERROR] {e}")


@router.message(lambda m: m.text == "⬅️ Назад")
async def back(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🚀 Подключиться")]],
        resize_keyboard=True
    )
    await message.answer("Главное меню:", reply_markup=kb)