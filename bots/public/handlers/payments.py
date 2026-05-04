from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from services.payment_service import create_payment, check_payment
from services.vpn_service import activate_access, get_vpn_link

router = Router()


# =========================
# CREATE PAYMENT
# =========================

@router.message(lambda m: m.text == "/pay")
async def pay(message: types.Message, state: FSMContext):

    data = await state.get_data()

    username = data.get("username")
    plan = data.get("plan")

    if not username or not plan:
        await message.answer("❌ Нет данных для оплаты")
        return

    try:
        payment = create_payment(plan, username)

        # сохраняем payment_id (ВАЖНО FIX)
        await state.update_data(payment_id=payment["payment_id"])

        await message.answer(
            f"💳 Оплата {payment['amount']} RUB\n\n"
            f"👉 {payment['url']}\n\n"
            f"После оплаты нажмите /check"
        )

    except Exception as e:
        print("PAY ERROR:", e)
        await message.answer("❌ Ошибка оплаты")


# =========================
# CHECK PAYMENT
# =========================

@router.message(lambda m: m.text == "/check")
async def check(message: types.Message, state: FSMContext):

    data = await state.get_data()

    username = data.get("username")
    plan = data.get("plan")
    payment_id = data.get("payment_id")

    if not all([username, plan, payment_id]):
        await message.answer("❌ Нет данных платежа")
        return

    try:
        if not check_payment(payment_id):
            await message.answer("❌ Платёж не найден")
            return

        activate_access(username, plan)

        vpn = get_vpn_link(username)

        await message.answer(
            f"✅ Оплата подтверждена\n\n"
            f"👤 {vpn['username']}\n"
            f"🔑 {vpn['password']}\n"
            f"🌐 {vpn['link']}\n"
            f"⏳ {vpn['expires_at']}"
        )

        await state.clear()

    except Exception as e:
        print("CHECK ERROR:", e)
        await message.answer("❌ Ошибка проверки")