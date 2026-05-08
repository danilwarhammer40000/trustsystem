from fastapi import APIRouter, Request
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.control_plane import activate_paid_plan
from services.public_user_service import get_or_create
from services.vpn_service import get_vpn_link

router = APIRouter()
bot = Bot(token=PUBLIC_BOT_TOKEN)


def normalize_link(link: str) -> str:
    """
    Убирает мусор от trusttunnel_endpoint
    """
    if not link:
        return ""

    # отсекаем любые debug/cli хвосты
    bad_markers = [
        "To connect on mobile",
        "scan QR code",
        "scan QR",
        "http://",
        "https://"
    ]

    # оставляем только tt:// часть
    if "tt://" in link:
        link = link.split("tt://")[1]
        link = "tt://" + link.strip()

    return link.strip()


def extract_qr_token(link: str) -> str:
    """
    Берём чистый токен после tt://?
    """
    if "tt://?" in link:
        return link.split("tt://?")[1]
    return link.replace("tt://", "")


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "bad_json"}

    if data.get("event") != "payment.succeeded":
        return {"status": "ignored"}

    meta = data.get("object", {}).get("metadata", {})

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
        activate_paid_plan(username, plan)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    try:
        vpn = get_vpn_link(username)

        link = normalize_link(vpn.get("link", ""))
        qr_token = extract_qr_token(link)

        qr_url = f"https://trusttunnel.org/qr.html#tt={qr_token}"

        text = (
            f"👤 {vpn['username']}\n"
            f"🔑 {vpn['password']}\n"
            f"⏳ {vpn['expires_at']}\n\n"
            f"🔗 {link}\n\n"
            f"To connect on mobile:\n{qr_url}"
        )

        await bot.send_message(
            chat_id=tg_id,
            text=text,
            disable_web_page_preview=True
        )

    except Exception as e:
        print("Telegram send error:", e)

    return {"status": "ok"}