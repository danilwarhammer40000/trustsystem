from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from services.payment_service import create_payment
from services.public_user_service import get_or_create_user_by_tg, activate_trial_by_tg
from services.vpn_service import get_vpn_link

router = Router()


@router.message(PaymentState.waiting_username)
async def get_username(message: types.Message, state: FSMContext):

    username = message.text.strip()

    await state.update_data(username=username)
    await state.set_state(PaymentState.ready_to_pay)

    await message.answer("Нажмите /pay")


@router.message(F.text == "/pay")
async def pay(message: types.Message, state: FSMContext):

    data = await state.get_data()

    tg_id = message.from_user.id
    username = data["username"]
    plan = data["plan"]

    # FREE
    if plan == "3":

        try:
            activate_trial_by_tg(tg_id)
        except:
            return await message.answer("❌ Trial уже использован")

        user = get_or_create_user_by_tg(tg_id, username)
        vpn = get_vpn_link(user["username"])

        return await message.answer(
            f"🎁 Активировано\n\n{vpn['link']}"
        )

    # PAID
    user = get_or_create_user_by_tg(tg_id, username)

    payment = create_payment(plan, user["username"])

    await message.answer(
        f"💳 Оплата: {payment['amount']} RUB\n\n{payment['url']}"
    )