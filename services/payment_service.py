import uuid
import json
from datetime import datetime

from yookassa import Configuration, Payment
from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


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


def create_payment(plan: str, tg_id: int):

    prices = {
        "30": 199,
        "60": 349
    }

    amount = prices.get(plan)
    if not amount:
        raise ValueError("INVALID_PLAN")

    username = f"user_{tg_id}"

    payment = Payment.create({
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"
        },
        "capture": True,
        "description": "VPN access",
        "metadata": {
            "tg_id": str(tg_id),
            "plan": plan,
            "username": username
        }
    }, uuid.uuid4())

    data = load()

    data.append({
        "id": payment.id,
        "tg_id": tg_id,
        "username": username,
        "plan": plan,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    })

    save(data)

    return {
        "url": payment.confirmation.confirmation_url,
        "amount": amount,
        "payment_id": payment.id
    }


def mark_paid(payment_id: str):
    data = load()

    for p in data:
        if p["id"] == payment_id:

            if p["status"] == "paid":
                return None

            p["status"] = "paid"
            p["paid_at"] = datetime.utcnow().isoformat()

            save(data)
            return p

    return None