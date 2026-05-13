import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user,
    extend_user,
    get_user_by_tg
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import is_paid, mark_paid

from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)


# =========================================
# 💳 PAYMENT PIPELINE (CLEAN TG-ID ONLY)
# =========================================

async def process_successful_payment(
    user_id: int,
    plan: str,
    payment_id: str
) -> None:
    try:
        tg_id = int(user_id)

        logger.info(f"[WEBHOOK] payment={payment_id} user={tg_id} plan={plan}")

        # 1. idempotency
        if payment_id and is_paid(payment_id):
            logger.info(f"[SKIP] already processed {payment_id}")
            return

        # 2. ensure user exists
        user = create_user(tg_id)

        # 3. extend
        days = int(plan)
        updated = extend_user(tg_id, days)
        username = updated["username"]

        logger.info(f"[OK] extended {username} for {days} days")

        # 4. sync system
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        # 5. send vpn card
        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=tg_id,
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        # 6. mark payment
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"[SUCCESS] payment done {payment_id}")

    except Exception:
        logger.exception(f"[CRITICAL] payment={payment_id}")


# =========================================
# 🔄 SYNC WRAPPER
# =========================================

def sync_all_users():
    try:
        full_sync()
        restart_trusttunnel()
        logger.info("[SYNC] completed")
    except Exception as e:
        logger.error(f"[SYNC ERROR] {e}")


# =========================================
# 👤 LEGACY HELPERS (READ ONLY)
# =========================================

def get_user(username: str):
    from services.user_service import get_user_by_username
    return get_user_by_username(username)


def get_user_by_tg_id(tg_id: int):
    return get_user_by_tg(tg_id)


def extend_user_legacy(username: str, days: int):
    from services.user_service import get_user_by_username

    user = get_user_by_username(username)
    if not user:
        raise ValueError("User not found")

    tg_id = user.get("telegram_id")
    if not tg_id:
        raise ValueError("User has no telegram_id")

    return extend_user(int(tg_id), days)


# =========================================
# 🎁 TRIAL (FIXED)
# =========================================

async def give_trial(tg_id: int, days: int = 1):
    try:
        tg_id = int(tg_id)

        user = create_user(tg_id)

        if user.get("trial_used"):
            logger.info(f"[TRIAL] already used {tg_id}")
            return

        updated = extend_user(tg_id, days)
        updated["trial_used"] = True

        # persist trial flag via service layer (IMPORTANT FIX)
        from services.user_service import _update_user
        _update_user(updated)

        username = updated["username"]

        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=tg_id,
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        logger.info(f"[TRIAL] {tg_id} granted {days} days")

    except Exception:
        logger.exception(f"[TRIAL ERROR] {tg_id}")