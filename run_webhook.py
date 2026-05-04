from aiohttp import web
from services.payment_webhook import handle_webhook

app = web.Application()
app.router.add_post("/yookassa", handle_webhook)

web.run_app(app, port=8080)