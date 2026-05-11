from fastapi import APIRouter, Request, HTTPException
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.control_plane import activate_paid_plan

router = APIRouter(prefix="/webhook")

bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()
    print("YOOKASSA WEBHOOK:", data)

    event = data.get("event")
    obj = data.get("object", {})

    if event != "payment.succeeded":
        return {"ok": True}

    payment_id = obj.get("id")
    metadata = obj.get("metadata", {})

    user_id = metadata.get("user_id")
    plan = metadata.get("plan")

    if not user_id or not plan:
        raise HTTPException(status_code=400, detail="Missing metadata")

    try:
        card_text = await activate_paid_plan(
            user_id=user_id,
            plan=plan,
            payment_id=payment_id
        )

        await bot.send_message(
            chat_id=int(user_id),
            text=card_text,
            parse_mode="HTML"
        )

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Internal error")

    return {"ok": True}