import uuid
import json
import threading
from datetime import datetime

from yookassa import Configuration, Payment
from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

FILE = "storage/payments.json"
lock = threading.Lock()


# =========================
# STORAGE
# =========================

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(data):
    with lock:
        tmp_file = FILE + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        import os
        os.replace(tmp_file, FILE)


# =========================
# PAYMENT CREATE
# =========================

def create_payment(plan: str, tg_id: int):
    prices = {
        "30": 10,
        "60": 20
    }

    amount = prices.get(plan)
    if amount is None:
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
                "return_url": "https://t.me/vpn_trusttunnel_bot"
            },
            "capture": True,
            "description": "VPN access",
            "metadata": {
                "user_id": str(tg_id),   # ❗ КРИТИЧНО: единый ключ для webhook
                "plan": plan,
                "username": username
            }
        },
        idempotence_key
    )

    data = load()

    # защита от дублей
    data.append({
        "id": payment.id,
        "user_id": str(tg_id),
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
# SAFE HELPERS
# =========================

def get_payment(payment_id: str):
    data = load()

    for p in data:
        if p.get("id") == payment_id:
            return p

    return None