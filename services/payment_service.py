import uuid
import json
from datetime import datetime

from yookassa import Configuration, Payment
from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

FILE = "storage/payments.json"


# =========================
# STORAGE
# =========================

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# =========================
# PAYMENT CREATE
# =========================

def create_payment(plan: str, tg_id: int):

    prices = {
        "30": 10,
        "60": 20
    }

    amount = prices.get(plan)
    if not amount:
        raise ValueError("INVALID_PLAN")

    username = f"user_{tg_id}"

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
        "created_at": datetime.utcnow().isoformat(),
        "paid_at": None
    })

    save(data)

    return {
        "url": payment.confirmation.confirmation_url,
        "amount": amount,
        "payment_id": payment.id
    }


# =========================
# PAYMENT STATUS
# =========================

def mark_paid(payment_id: str):
    data = load()

    for p in data:
        if p.get("id") == payment_id:

            # idempotency
            if p.get("status") == "paid":
                return p

            p["status"] = "paid"
            p["paid_at"] = datetime.utcnow().isoformat()

            save(data)
            return p

    return None


def is_paid(payment_id: str) -> bool:
    data = load()

    for p in data:
        if p.get("id") == payment_id:
            return p.get("status") == "paid"

    return False