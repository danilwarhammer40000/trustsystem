from fastapi import APIRouter, Request

from services.payment_service import mark_paid
from services.vpn_service import activate_access

router = APIRouter()


@router.post("/api/payment_webhook/yookassa")
async def yookassa_webhook(request: Request):

    data = await request.json()

    print("YOOKASSA WEBHOOK:", data)

    event = data.get("event")
    obj = data.get("object", {})

    if event != "payment.succeeded":
        return {"status": "ignored"}

    payment_id = obj.get("id")

    metadata = obj.get("metadata", {})

    username = metadata.get("username")
    plan = metadata.get("plan")

    if not username or not plan:
        print("❌ BAD METADATA")
        return {"status": "bad_metadata"}

    updated = mark_paid(payment_id)

    if updated:
        activate_access(username, plan)
        print(f"✅ VPN ACTIVATED: {username}")

    return {"status": "ok"}