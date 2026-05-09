from services.user_service import (
    get_user,
    activate_paid,
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import mark_paid, is_paid

from core.sync import full_sync, restart_trusttunnel


# =========================
# ACTIVATE PLAN
# =========================

async def activate_paid_plan(
    username: str,
    plan: str,
    payment_id: str | None = None
) -> str:
    """
    ЕДИНАЯ ТОЧКА БИЗНЕС-ЛОГИКИ
    """

    # 1. idempotency платежа
    if payment_id:
        if is_paid(payment_id):
            return "⚠️ Платёж уже обработан"
        mark_paid(payment_id)

    # 2. пользователь
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    # 3. тариф
    try:
        days = int(plan)
    except Exception:
        raise ValueError("INVALID_PLAN")

    # 4. активация
    updated_user = activate_paid(username, days)
    if not updated_user:
        raise ValueError("ACTIVATION_FAILED")

    # 5. синк системы ПОСЛЕ активации
    full_sync()
    restart_trusttunnel()

    # 6. карточка
    card = build_vpn_card(username)

    if not card or "text" not in card:
        raise ValueError("CARD_BUILD_FAILED")

    return card["text"]


# =========================
# GLOBAL SYNC (ВАЖНО)
# =========================

def sync_all_users():
    """
    ЕДИНАЯ ТОЧКА синхронизации для:
    - admin bot
    - scheduler
    """
    full_sync()
    restart_trusttunnel()
    return "✅ Sync completed"