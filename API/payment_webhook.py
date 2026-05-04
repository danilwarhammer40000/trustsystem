# api/payment_webhook.py

from fastapi import APIRouter, Request
from services.payment_service import mark_paid
from services.public_user_service import get_or_create_user_by_tg
from services.vpn_service import activate_access

router = APIRouter()


@router.post("/payment/webhook")
async def webhook(request: Request):

    data = await request.json()

    if data.get("event") != "payment.succeeded":
        return {"ok": True}

    obj = data.get("object", {})

    payment_id = obj.get("id")
    metadata = obj.get("metadata", {})

    username = metadata.get("username")
    plan = metadata.get("plan")

    if not username:
        return {"error": "no username"}

    if mark_paid(payment_id):

        # активируем доступ через старую систему (НЕ ЛОМАЕМ)
        activate_access(username, plan)

    return {"ok": True}