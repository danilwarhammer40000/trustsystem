import uuid
from yoomoney import Quickpay, Client

from config.settings import YOOMONEY_RECEIVER


# =========================
# PRICES
# =========================

PRICES = {
    "30": 199,
    "60": 349
}


# =========================
# CREATE PAYMENT
# =========================

def create_payment(plan: str, username: str):
    """
    Создаёт платёж и возвращает ссылку
    """

    if plan not in PRICES:
        raise ValueError("INVALID_PLAN")

    amount = PRICES[plan]

    label = f"{username}:{plan}:{uuid.uuid4().hex}"

    quickpay = Quickpay(
        receiver=YOOMONEY_RECEIVER,
        quickpay_form="shop",
        targets=f"VPN {plan} days",
        paymentType="SB",  # СБП / карта
        sum=amount,
        label=label
    )

    return {
        "url": quickpay.base_url,
        "label": label,
        "amount": amount
    }


# =========================
# CHECK PAYMENT
# =========================

def check_payment(token: str, label: str):
    """
    Проверка оплаты через API ЮMoney
    token — это API токен кошелька
    """

    client = Client(token)

    history = client.operation_history(label=label)

    for op in history.operations:
        if op.status == "success":
            return True

    return False