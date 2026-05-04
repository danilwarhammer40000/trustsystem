from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bots.public.states.payment import PaymentState
from services.payment_service import create_payment

router = Router()


@router.message(PaymentState.waiting_username)
async def get_username(message: types.Message, state: FSMContext):
    username = message.text.strip()

    await state.update_data(username=username)
    await state.set_state(PaymentState.ready_to_pay)

    await message.answer("Нажмите /pay для оплаты")


@router.message(Command("pay"))
async def pay(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if not data.get("plan") or not data.get("username"):
        return await message.answer("❌ Сначала выберите тариф")

    # 🎁 бесплатный тариф
    if data["plan"] == "3":
        return await message.answer("🎁 Бесплатный доступ активирован (заглушка)")

    payment = create_payment(
        plan=data["plan"],
        username=data["username"]
    )

    await message.answer(
        f"💳 Оплата {payment['amount']} RUB\n\n"
        f"👉 {payment['url']}\n\n"
        f"После оплаты доступ будет выдан автоматически"
    )