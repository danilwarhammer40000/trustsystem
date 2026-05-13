import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user,
    extend_user,
    get_user_by_tg,
    get_all_users,
    save_users
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
    user_id: int,
    plan: str,
    payment_id: str
) -> None:
    try:
        logger.info(f"[WEBHOOK] payment={payment_id} user={user_id} plan={plan}")

        tg_id = int(user_id)

        # 1. идемпотентность
        if payment_id and is_paid(payment_id):
            logger.info(f"[SKIP] already processed {payment_id}")
            return

        # 2. user
        user = create_user(tg_id)

        # 3. план
        days = int(plan)

        # 4. продление
        updated_user = extend_user(tg_id, days)
        username = updated_user.get("username")

        logger.info(f"[OK] extended {username} for {days} days")

        # 5. sync
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        # 6. VPN
        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=tg_id,
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        # 7. mark paid
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"[SUCCESS] payment done {payment_id}")

    except Exception:
        logger.exception(f"[CRITICAL] payment={payment_id}")


# =========================================
# 🔄 SYNC
# =========================================

def sync_all_users():
    try:
        full_sync()
        restart_trusttunnel()
        logger.info("[SYNC] all users synced")
    except Exception as e:
        logger.error(f"[SYNC ERROR] {e}")


# =========================================
# 👤 USER OPERATIONS (LEGACY COMPAT)
# =========================================

def extend_user_legacy(username: str, days: int):
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            tg_id = u.get("telegram_id")
            if tg_id:
                return extend_user(int(tg_id), days)

    raise ValueError("User not found")


def get_user(username: str):
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            return u

    return None


def get_user_by_tg_id(tg_id: int):
    return get_user_by_tg(int(tg_id))


# =========================================
# 🎁 TRIAL
# =========================================

async def give_trial(tg_id: int, days: int = 1):
    try:
        tg_id = int(tg_id)

        user = create_user(tg_id)

        if user.get("trial_used"):
            logger.info(f"[TRIAL] already used {tg_id}")
            return

        updated_user = extend_user(tg_id, days)
        updated_user["trial_used"] = True

        # сохранить флаг
        users = get_all_users()
        for i, u in enumerate(users):
            if u.get("telegram_id") == tg_id:
                users[i] = updated_user
                break
        save_users(users)

        username = updated_user.get("username")

        # sync
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[SYNC ERROR] {e}")

        # vpn
        try:
            card = build_vpn_card(username)

            await bot.send_message(
                chat_id=tg_id,
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"[VPN ERROR] {e}")

        logger.info(f"[TRIAL] {tg_id} got {days} days")

    except Exception:
        logger.exception(f"[TRIAL ERROR] {tg_id}")


# =========================================
# 🔧 ADMIN
# =========================================

def set_expire(username: str, expires_at: str):
    users = get_all_users()

    for u in users:
        if u.get("username") == username:
            u["expires_at"] = expires_at
            u["status"] = "active"

            save_users(users)
            return u

    raise ValueError("User not found")