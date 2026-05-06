from fastapi import APIRouter, Request
from aiogram import Bot
from config.settings import PUBLIC_BOT_TOKEN
from services.vpn_service import activate_access
from services.public_user_service import get_by_tg

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()

    event = data.get("event")
    obj = data.get("object", {})

    if event != "payment.succeeded":
        return {"status": "ignored"}

    meta = obj.get("metadata", {})

    username = meta.get("username")
    plan = meta.get("plan")
    tg_id = meta.get("tg_id")

    if not all([username, plan, tg_id]):
        return {"status": "missing_metadata"}

    # 1. активируем VPN
    user = activate_access(username, plan)

    # 2. обновляем пользователя
    db_user = get_by_tg(int(tg_id))

    # 3. уведомляем в Telegram
    try:
        await bot.send_message(
            chat_id=int(tg_id),
            text=(
                "✅ Оплата подтверждена\n\n"
                "🔐 VPN активирован\n"
                f"📅 Тариф: {plan} дней\n"
                f"⏳ До: {user.get('expires_at')}"
            )
        )
    except Exception as e:
        print("Telegram send error:", e)

    return {"status": "ok"}