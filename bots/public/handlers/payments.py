from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from services.payment_service import create_payment
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

    payment = create_payment(plan, username)

    await state.update_data(label=payment["label"])

    await message.answer(
        f"💳 Оплата {payment['amount']} RUB\n\n"
        f"👉 {payment['url']}\n\n"
        f"После оплаты нажмите /check"
    )


# =========================
# CHECK PAYMENT
# =========================

@router.message(lambda m: m.text == "/check")
async def check(message: types.Message, state: FSMContext):

    from config.settings import YOOMONEY_TOKEN
    from services.payment_service import check_payment

    data = await state.get_data()

    username = data.get("username")
    plan = data.get("plan")
    label = data.get("label")

    if not all([username, plan, label]):
        await message.answer("❌ Нет данных платежа")
        return

    if not check_payment(YOOMONEY_TOKEN, label):
        await message.answer("❌ Платёж не найден")
        return

    # активируем доступ
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