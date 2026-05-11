from services.user_service import (
    get_user,
    activate_paid,
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import mark_paid, is_paid

from core.sync import full_sync, restart_trusttunnel


# =========================
# ACTIVATE PLAN (FIXED FLOW)
# =========================

async def activate_paid_plan(
    username: str,
    plan: str,
    payment_id: str | None = None
) -> str:

    # 1. idempotency (ТОЛЬКО CHECK)
    if payment_id and is_paid(payment_id):
        return "⚠️ Платёж уже обработан"

    # 2. user check
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    # 3. plan parsing
    try:
        days = int(plan)
    except:
        raise ValueError("INVALID_PLAN")

    # 4. ACTIVATE USER
    updated_user = activate_paid(username, days)
    if not updated_user:
        raise ValueError("ACTIVATION_FAILED")

    # 5. sync AFTER activation
    full_sync()
    restart_trusttunnel()

    # 6. build card
    card = build_vpn_card(username)
    if not card or "text" not in card:
        raise ValueError("CARD_BUILD_FAILED")

    # 7. mark payment ONLY AFTER SUCCESS
    if payment_id:
        mark_paid(payment_id)

    return card["text"]