import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user_if_not_exists,
    extend_user_by_tg,
    get_user_by_tg,
    get_all_users
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import is_paid, mark_paid

from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)


# =========================================
# 💳 ОСНОВНОЙ ФЛОУ (WEBHOOK)
# =========================================

async def process_successful_payment(
    user_id: str,
    plan: str,
    payment_id: str
) -> None:
    try:
        logger.info(f"[WEBHOOK] payment={payment_id} user={user_id} plan={plan}")

        # 1. Идемпотентность
        if payment_id and is_paid(payment_id):
            logger.info(f"[SKIP] already processed {payment_id}")
            return

        # 2. USER (TG ID = истина)
        user = create_user_if_not_exists(user_id)

        # 3. План
        days = int(plan)

        # 4. Продление
        updated_user = extend_user_by_tg(user_id, days)
        username = updated_user.get("username")

        logger.info(f"[OK] extended {username} for {days} days")

        # 5. Sync
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        # 6. VPN
        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=int(user_id),
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        # 7. mark paid
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"[SUCCESS] payment done {payment_id}")

    except Exception as e:
        logger.exception(f"[CRITICAL] payment={payment_id}")


# =========================================
# 🔄 SYNC (СТАРЫЙ API ДЛЯ БОТОВ / WORKER)
# =========================================

def sync_all_users():
    try:
        full_sync()
        restart_trusttunnel()
        logger.info("[SYNC] all users synced")
    except Exception as e:
        logger.error(f"[SYNC ERROR] {e}")


# =========================================
# 👤 USER OPERATIONS (совместимость)
# =========================================

def extend_user(username: str, days: int):
    """
    Старый API (через username)
    """
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            tg_id = u.get("tg_id")
            if tg_id:
                return extend_user_by_tg(str(tg_id), days)

    raise ValueError("User not found")


def get_user(username: str):
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            return u

    return None


def get_user_by_tg_id(tg_id: str):
    return get_user_by_tg(tg_id)


# =========================================
# 🎁 TRIAL LOGIC
# =========================================

async def give_trial(tg_id: str, days: int = 1):
    try:
        user = create_user_if_not_exists(tg_id)

        updated_user = extend_user_by_tg(tg_id, days)
        username = updated_user.get("username")

        # sync
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        # send vpn
        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=int(tg_id),
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        logger.info(f"[TRIAL] {tg_id} got {days} days")

    except Exception as e:
        logger.exception(f"[TRIAL ERROR] {tg_id}")


# =========================================
# 🔧 ADMIN COMPAT (НЕ УДАЛЯТЬ!)
# =========================================

def set_expire(username: str, expires_at: str):
    """
    Нужно для admin-бота
    """
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            u["expires_at"] = expires_at
            u["status"] = "active"

            from services.user_service import save_users
            save_users(users)

            return u

    raise ValueError("User not found")