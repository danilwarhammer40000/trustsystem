import uuid
import json
from yookassa import Configuration, Payment

from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

FILE = "storage/payments.json"


def load():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return []


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_payment(plan, username):
    prices = {"30": 199, "60": 349}
    amount = prices[plan]

    payment = Payment.create({
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/your_bot"},
        "capture": True,
        "description": f"{username}:{plan}"
    }, uuid.uuid4())

    data = load()

    data.append({
        "id": payment.id,
        "username": username,
        "plan": plan,
        "status": "pending"
    })

    save(data)

    return {
        "url": payment.confirmation.confirmation_url,
        "amount": amount
    }


def mark_paid(payment_id):
    data = load()

    for p in data:
        if p["id"] == payment_id:
            if p["status"] == "paid":
                return False
            p["status"] = "paid"

    save(data)
    return True