from aiogram import Router, types

from services.vpn_service import activate_access, get_vpn_link

router = Router()


# ⚠️ здесь нужно подключить реальную оплату
# сейчас — эмуляция


@router.message(lambda m: m.text == "/pay")
async def fake_payment(message: types.Message):

    # ⚠️ В реале ты должен брать это из БД или FSM
    username = "test"   # заменить на реального пользователя
    plan = "30"         # заменить

    try:
        activate_access(username, plan)

        vpn = get_vpn_link(username)

        await message.answer(
            f"✅ Оплата прошла\n\n"
            f"👤 {vpn['username']}\n"
            f"🔑 {vpn['password']}\n"
            f"🌐 {vpn['link']}\n"
            f"⏳ {vpn['expires_at']}"
        )

    except Exception as e:
        await message.answer("❌ Ошибка оплаты")
        print("PAY ERROR:", e)