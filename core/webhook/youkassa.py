from fastapi import APIRouter, Request
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.control_plane import activate_paid_plan
from services.public_user_service import get_or_create

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "bad_json"}

    if data.get("event") != "payment.succeeded":
        return {"status": "ignored"}

    obj = data.get("object", {})
    meta = obj.get("metadata", {})

    tg_id = meta.get("tg_id")
    plan = meta.get("plan")

    if not tg_id or not plan:
        return {"status": "missing_metadata"}

    try:
        tg_id = int(tg_id)
    except Exception:
        return {"status": "invalid_tg_id"}

    user = get_or_create(tg_id)
    if not user:
        return {"status": "user_create_failed"}

    username = user.get("username")
    if not username:
        return {"status": "no_username"}

    try:
        # CONTROL PLANE RETURNS FINAL OUTPUT
        card_text = await activate_paid_plan(username=username, plan=plan)

        await bot.send_message(
            chat_id=tg_id,
            text=card_text,
            disable_web_page_preview=True
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}