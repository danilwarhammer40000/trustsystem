import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user,
    extend_user,
    get_user_by_tg,
    get_user_by_username
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import is_paid, mark_paid
from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)


# =========================
# PAYMENT PIPELINE
# =========================

async def process_successful_payment(user_id: int, plan: str, payment_id: str):
    try:
        tg_id = int(user_id)

        if payment_id and is_paid(payment_id):
            return

        user = create_user(tg_id)
        updated = extend_user(tg_id, int(plan))
        username = updated["username"]

        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"sync error {e}")

        try:
            card = build_vpn_card(username)
            await bot.send_message(tg_id, card["text"], parse_mode="HTML")
        except Exception as e:
            logger.error(f"vpn error {e}")

        if payment_id:
            mark_paid(payment_id)

    except Exception:
        logger.exception("payment crash")


# =========================
# SYNC WRAPPER
# =========================

def sync_all_users():
    try:
        full_sync()
        restart_trusttunnel()
    except Exception as e:
        logger.error(e)


# =========================
# LEGACY HELPERS
# =========================

def get_user(username: str):
    return get_user_by_username(username)


def get_user_by_tg_id(tg_id: int):
    return get_user_by_tg(tg_id)


def extend_user_legacy(username: str, days: int):
    user = get_user_by_username(username)
    return extend_user(user["telegram_id"], days)


# =========================
# TRIAL FIXED
# =========================

async def give_trial(tg_id: int, days: int = 1):
    user = create_user(tg_id)

    if user.get("trial_used"):
        return

    updated = extend_user(tg_id, days)
    updated["trial_used"] = True

    from services.user_service import _update_user
    _update_user(updated)

    try:
        full_sync()
        restart_trusttunnel()
    except:
        pass

    card = build_vpn_card(updated["username"])
    await bot.send_message(tg_id, card["text"], parse_mode="HTML")