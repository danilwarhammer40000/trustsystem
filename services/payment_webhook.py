from aiohttp import web

from services.payment_service import mark_paid
from services.vpn_service import activate_access


async def handle_webhook(request):
    data = await request.json()

    if data.get("event") != "payment.succeeded":
        return web.Response(text="ok")

    obj = data.get("object", {})
    payment_id = obj.get("id")
    description = obj.get("description")

    username, plan = description.split(":")

    updated = mark_paid(payment_id)

    if updated:
        activate_access(username, plan)

    return web.Response(text="ok")