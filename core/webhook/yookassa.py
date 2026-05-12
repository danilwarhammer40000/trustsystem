from fastapi import APIRouter, Request, HTTPException
import logging
import hashlib
import hmac

from config.settings import YOOKASSA_API_KEY
from core.queue import push

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")


def verify_yookassa_signature(data: bytes, signature: str) -> bool:
    """Проверка подписи от YooKassa"""
    if not signature:
        return False

    secret = YOOKASSA_API_KEY.encode()
    computed = hmac.new(secret, data, hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed, signature)


@router.post("/yookassa")
async def yookassa_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Yookassa-Signature")

    try:
        data = await request.json()

        event = data.get("event")
        obj = data.get("object", {})

        payment_id = obj.get("id")

        logger.info(
            f"YOOKASSA WEBHOOK: event={event} payment_id={payment_id}"
        )

        # 🔐 Верификация подписи
        if not verify_yookassa_signature(body, signature):
            logger.warning("Invalid YooKassa signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # 🟢 Только успешные платежи
        if event != "payment.succeeded":
            return {"ok": True}

        metadata = obj.get("metadata", {})

        user_id = metadata.get("user_id")
        plan = metadata.get("plan")

        if not user_id or not plan:
            logger.error(f"Missing metadata in payment {payment_id}")
            raise HTTPException(status_code=400, detail="Missing metadata")

        # 🔥 КЛЮЧЕВОЕ: кладём в очередь
        push({
            "type": "payment",
            "user_id": str(user_id),
            "plan": str(plan),
            "payment_id": payment_id
        })

        logger.info(f"Payment {payment_id} queued")

        return {"ok": True}

    except HTTPException:
        raise

    except Exception:
        logger.exception("Webhook error")
        raise HTTPException(status_code=500, detail="Internal error")