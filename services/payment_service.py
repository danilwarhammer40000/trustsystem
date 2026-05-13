import uuid
import json
import threading
import os
from datetime import datetime
from typing import Optional, Dict, List

from yookassa import Configuration, Payment
from config.settings import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

FILE = "/opt/trustsystem/storage/payments.json"
lock = threading.Lock()


# =========================
# STORAGE
# =========================

def load() -> List[Dict]:
    if not os.path.exists(FILE):
        return []

    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save(data: List[Dict]):
    with lock:
        tmp_file = FILE + ".tmp"

        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        os.replace(tmp_file, FILE)


# =========================
# PAYMENT CREATE
# =========================

def create_payment(plan: str, tg_id: int):
    prices = {
        "30": 1,
        "60": 20
    }

    amount = prices.get(plan)
    if amount is None:
        raise ValueError("INVALID_PLAN")

    tg_id = int(tg_id)
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
                "user_id": str(tg_id),  # для webhook
                "plan": plan
            }
        },
        idempotence_key
    )

    data = load()

    # защита от дублей
    if any(p.get("id") == payment.id for p in data):
        return {
            "url": payment.confirmation.confirmation_url,
            "amount": amount,
            "payment_id": payment.id
        }

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

def mark_paid(payment_id: str) -> Optional[Dict]:
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
# HELPERS
# =========================

def get_payment(payment_id: str) -> Optional[Dict]:
    data = load()

    for p in data:
        if p.get("id") == payment_id:
            return p

    return None


def get_user_payments(tg_id: int) -> List[Dict]:
    data = load()
    tg_id = int(tg_id)

    return [p for p in data if p.get("tg_id") == tg_id]