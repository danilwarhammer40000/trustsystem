from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from aiogram import Bot
import logging
import hashlib
import hmac

from config.settings import PUBLIC_BOT_TOKEN, YOOKASSA_API_KEY
from services.control_plane import process_successful_payment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")
bot = Bot(token=PUBLIC_BOT_TOKEN)


def verify_yookassa_signature(data: bytes, signature: str) -> bool:
    """Проверка подписи от YooKassa"""
    if not signature:
        return False
    secret = YOOKASSA_API_KEY.encode()
    computed = hmac.new(secret, data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


@router.post("/yookassa")
async def yookassa_webhook(request: Request, background: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Yookassa-Signature")

    try:
        data = await request.json()
        logger.info(f"YOOKASSA WEBHOOK received: {data.get('event')} | payment_id={data.get('object', {}).get('id')}")

        # Верификация подписи (важно!)
        if not verify_yookassa_signature(body, signature):
            logger.warning("Invalid YooKassa signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        event = data.get("event")
        obj = data.get("object", {})

        if event != "payment.succeeded":
            return {"ok": True}

        payment_id = obj.get("id")
        metadata = obj.get("metadata", {})

        user_id = metadata.get("user_id")
        plan = metadata.get("plan")

        if not user_id or not plan:
            logger.error(f"Missing metadata in payment {payment_id}")
            raise HTTPException(status_code=400, detail="Missing metadata")

        # Асинхронная обработка (чтобы webhook отвечал быстро)
        background.add_task(
            process_successful_payment,
            user_id=str(user_id),
            plan=str(plan),
            payment_id=payment_id
        )

        return {"ok": True}

    except Exception as e:
        logger.exception("Webhook error")
        raise HTTPException(status_code=500, detail="Internal error")