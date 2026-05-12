import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user_if_not_exists,
    extend_user_by_tg
)

from services.vpn_card_builder import build_vpn_card
from services.payment_service import is_paid, mark_paid

from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)


# =========================
# MAIN PAYMENT PROCESSING
# =========================

async def process_successful_payment(
    user_id: str,
    plan: str,
    payment_id: str
) -> None:
    """
    ПРОДАКШН webhook обработчик (неубиваемый)
    """

    try:
        logger.info(f"[WEBHOOK] payment={payment_id} user={user_id} plan={plan}")

        # =========================
        # 1. ИДЕМПОТЕНТНОСТЬ
        # =========================
        if payment_id and is_paid(payment_id):
            logger.info(f"[SKIP] Payment {payment_id} already processed")
            return

        # =========================
        # 2. ГАРАНТИЯ USER
        # =========================
        user = create_user_if_not_exists(user_id)

        if not user:
            logger.error(f"[FATAL] Cannot create/find user {user_id}")
            return

        # =========================
        # 3. ПАРСИНГ ПЛАНА
        # =========================
        try:
            days = int(plan)
        except Exception:
            logger.error(f"[ERROR] Invalid plan: {plan}")
            return

        # =========================
        # 4. ПРОДЛЕНИЕ
        # =========================
        updated_user = extend_user_by_tg(user_id, days)

        if not updated_user:
            logger.error(f"[ERROR] extend_user failed for {user_id}")
            return

        username = updated_user.get("username")

        logger.info(f"[OK] User {username} extended for {days} days")

        # =========================
        # 5. СИНХРОНИЗАЦИЯ
        # =========================
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"[WARN] sync failed: {e}")

        # =========================
        # 6. ВЫДАЧА КОНФИГА
        # =========================
        try:
            card = build_vpn_card(username)

            if card and "text" in card:
                await bot.send_message(
                    chat_id=int(user_id),
                    text=card["text"],
                    parse_mode="HTML"
                )
            else:
                logger.error(f"[ERROR] card build failed for {username}")

        except Exception as e:
            logger.error(f"[ERROR] send message failed: {e}")

        # =========================
        # 7. ФИКСАЦИЯ ПЛАТЕЖА
        # =========================
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"[SUCCESS] payment {payment_id} done for {user_id}")

    except Exception as e:
        logger.exception(f"[CRITICAL] payment processing failed: {payment_id}")