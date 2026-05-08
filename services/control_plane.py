from services.user_service import (
    get_user,
    activate_paid,
    extend_user,
    activate_trial,
)

from services.vpn_card_bilder import build_vpn_card
from services.payment_service import mark_paid


async def activate_paid_plan(username: str, plan: str, payment_id: str | None = None):
    """
    ЕДИНАЯ ТОЧКА БИЗНЕС-ЛОГИКИ:
    - активация оплаты
    - обновление пользователя
    - генерация VPN-карты
    - возврат текста для Telegram
    """

    # 1. отметить оплату (idempotency защита)
    if payment_id:
        mark_paid(payment_id)

    # 2. проверить пользователя
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    # 3. определить длительность тарифа
    try:
        days = int(plan)
    except:
        raise ValueError("INVALID_PLAN")

    # 4. активировать/продлить пользователя
    # ВАЖНО: используем только user_service (источник истины)
    updated_user = activate_paid(username, days)

    if not updated_user:
        raise ValueError("ACTIVATION_FAILED")

    # 5. собрать VPN карточку (единственный output слой)
    card = build_vpn_card(username)

    # 6. вернуть только текст (presentation готовится тут)
    return card["text"]