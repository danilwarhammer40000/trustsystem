import uuid
from yookassa import Configuration, Payment

from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


# =========================
# CONFIG
# =========================

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY


# =========================
# PRICES
# =========================

PRICES = {
    "30": 180,
    "60": 300
}


# =========================
# CREATE PAYMENT
# =========================

def create_payment(plan: str, username: str):
    if plan not in PRICES:
        raise ValueError("INVALID_PLAN")

    amount = PRICES[plan]
    payment_id = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"
        },
        "capture": True,
        "description": f"{username} VPN {plan} days"
    }, payment_id)

    return {
        "payment_id": payment.id,
        "url": payment.confirmation.confirmation_url,
        "amount": amount
    }


# =========================
# CHECK PAYMENT
# =========================

def check_payment(payment_id: str):
    payment = Payment.find_one(payment_id)

    if payment.status == "succeeded":
        return True

    return False