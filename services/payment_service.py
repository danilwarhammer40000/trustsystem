import uuid
import json
import threading
from datetime import datetime

from yookassa import Configuration, Payment
from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

FILE = "storage/payments.json"

# 🔒 защита от race condition при webhook
lock = threading.Lock()


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
    with lock:
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

    idempotence_key = str(uuid.uuid4())

    payment = Payment.create(
        {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me}"
            },
            "capture": True,
            "description": "VPN access",
            "metadata": {
                "tg_id": str(tg_id),
                "plan": plan,
                "username": username
            }
        },
        idempotence_key
    )

    data = load()

    # защита от дубля платежей
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

            # idempotency protection
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


# =========================
# SAFE HELPERS (WEBHOOK USE)
# =========================

def get_payment(payment_id: str):
    data = load()

    for p in data:
        if p.get("id") == payment_id:
            return p

    return None