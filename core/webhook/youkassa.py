from fastapi import APIRouter, Request
from services.payment_service import mark_paid
from services.vpn_service import activate_access

router = APIRouter()


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()

    event = data.get("event")
    obj = data.get("object", {})

    if event == "payment.succeeded":
        payment_id = obj.get("id")

        payment = mark_paid(payment_id)

        if payment:
            activate_access(
                payment["username"],
                payment["plan"]
            )

    return {"status": "ok"}