from fastapi import APIRouter, Request, HTTPException
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.control_plane import activate_paid_plan

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/youkassa")
async def youkassa_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = data.get("event")
    obj = data.get("object", {})

    # Нас интересует только успешная оплата
    if event != "payment.succeeded":
        return {"ok": True}

    # Данные платежа
    payment_id = obj.get("id")
    metadata = obj.get("metadata", {})

    username = metadata.get("username")
    plan = metadata.get("plan")

    if not username or not plan:
        raise HTTPException(status_code=400, detail="Missing metadata")

    try:
        # АКТИВАЦИЯ ТАРИФА
        card_text = await activate_paid_plan(
            username=username,
            plan=plan,
            payment_id=payment_id  # КРИТИЧНО
        )

        # ОТПРАВКА ПОЛЬЗОВАТЕЛЮ
        await bot.send_message(
            chat_id=username,
            text=card_text,
            parse_mode="HTML"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True}