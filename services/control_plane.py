from services.user_service import (
    get_user,
    activate_paid,
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import mark_paid, is_paid


async def activate_paid_plan(
    username: str,
    plan: str,
    payment_id: str | None = None
) -> str:
    """
    ЕДИНАЯ ТОЧКА БИЗНЕС-ЛОГИКИ:
    - обработка платежа (idempotent)
    - активация/продление пользователя
    - генерация VPN-карты
    - возврат текста для Telegram
    """

    # 1. защита от повторного webhook (idempotency)
    if payment_id:
        if is_paid(payment_id):
            return "⚠️ Платёж уже обработан"
        mark_paid(payment_id)

    # 2. получить пользователя
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    # 3. распарсить тариф
    try:
        days = int(plan)
    except Exception:
        raise ValueError("INVALID_PLAN")

    # 4. активировать (или продлить)
    updated_user = activate_paid(username, days)
    if not updated_user:
        raise ValueError("ACTIVATION_FAILED")

    # 5. собрать VPN карточку (ЕДИНСТВЕННОЕ место генерации QR/линка)
    card = build_vpn_card(username)

    if not card or "text" not in card:
        raise ValueError("CARD_BUILD_FAILED")

    # 6. вернуть готовый текст
    return card["text"]