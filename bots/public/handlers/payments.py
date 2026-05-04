from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from services.payment_service import create_payment, check_payment
from services.vpn_service import activate_access, get_vpn_link

router = Router()


@router.message(lambda m: m.text == "/pay")
async def pay(message: types.Message, state: FSMContext):

    data = await state.get_data()

    username = data.get("username")
    plan = data.get("plan")

    if not username or not plan:
        await message.answer("❌ Сначала выберите тариф")
        return

    payment = create_payment(plan, username)

    await state.update_data(payment_id=payment["payment_id"])

    await message.answer(
        f"💳 {payment['amount']} RUB\n\n{payment['url']}\n\nПосле оплаты нажмите /check"
    )


@router.message(lambda m: m.text == "/check")
async def check(message: types.Message, state: FSMContext):

    data = await state.get_data()

    username = data.get("username")
    plan = data.get("plan")
    payment_id = data.get("payment_id")

    if not all([username, plan, payment_id]):
        await message.answer("❌ Нет данных платежа")
        return

    if not check_payment(payment_id):
        await message.answer("❌ Платёж не найден")
        return

    activate_access(username, plan)

    vpn = get_vpn_link(username)

    await message.answer(
        f"✅ Оплачено\n\n"
        f"👤 {vpn['username']}\n"
        f"🔑 {vpn['password']}\n"
        f"🌐 {vpn['link']}\n"
        f"⏳ {vpn['expires_at']}"
    )

    await state.clear()