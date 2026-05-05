from fastapi import APIRouter, Request
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.payment_service import mark_paid
from services.vpn_service import activate_access
from services.public_user_service import get_by_tg

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()

    event = data.get("event")
    obj = data.get("object", {})

    if event == "payment.succeeded":
        payment_id = obj.get("id")

        payment = mark_paid(payment_id)

        if payment:
            # 1. активируем VPN
            activate_access(
                payment["username"],
                payment["plan"]
            )

            # 2. получаем пользователя
            user = get_by_tg(payment["tg_id"])

            if user:
                # 3. отправляем доступ
                await bot.send_message(
                    chat_id=payment["tg_id"],
                    text=(
                        "✅ Оплата прошла успешно\n\n"
                        "🔐 VPN активирован\n\n"
                        f"📅 Тариф: {payment['plan']} дней\n"
                        f"⏳ До: {user.get('expires_at')}"
                    )
                )

    return {"status": "ok"}