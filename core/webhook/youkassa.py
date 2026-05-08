from fastapi import APIRouter, Request
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.control_plane import activate_paid_plan
from services.public_user_service import get_or_create
from services.vpn_service import get_vpn_link

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "bad_json"}

    event = data.get("event")
    obj = data.get("object", {})

    if event != "payment.succeeded":
        return {"status": "ignored"}

    meta = obj.get("metadata", {})

    tg_id = meta.get("tg_id")
    plan = meta.get("plan")

    if not tg_id or not plan:
        return {"status": "missing_metadata"}

    try:
        tg_id = int(tg_id)
    except Exception:
        return {"status": "invalid_tg_id"}

    user_db = get_or_create(tg_id)

    if not user_db:
        return {"status": "user_create_failed"}

    username = user_db.get("username")

    if not username:
        return {"status": "no_username_in_db"}

    try:
        user = activate_paid_plan(username, plan)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"internal_error: {e}"}

    try:
        vpn = get_vpn_link(username)

        link_code = vpn["link"].replace("tt://?", "")

        text = (
            f"👤 {vpn['username']}\n"
            f"🔑 {vpn['password']}\n"
            f"⏳ {vpn['expires_at']}\n\n"
            f"🔗 {vpn['link']}\n\n"
            "To connect on mobile, scan QR:\n"
            f"https://trusttunnel.org/qr.html#tt={link_code}"
        )

        await bot.send_message(chat_id=tg_id, text=text)

    except Exception as e:
        print("Telegram send error:", e)

    return {"status": "ok"}