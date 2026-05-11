import logging
from datetime import datetime

from aiogram import Bot
from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import get_user, activate_paid
from services.vpn_card_builder import build_vpn_card
from services.payment_service import is_paid, mark_paid
from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)

bot = Bot(token=PUBLIC_BOT_TOKEN)


# =========================
# COMPATIBILITY LAYER (для старых ботов)
# =========================
def sync_all_users():
    """
    COMPAT LAYER: используется в bots/public/ и bots/admin/
    """
    try:
        full_sync()
        restart_trusttunnel()
        return "OK"
    except Exception as e:
        logger.error(f"sync_all_users failed: {e}")
        return "ERROR"


# =========================
# MAIN PAYMENT PROCESSING
# =========================
async def process_successful_payment(
    user_id: str,
    plan: str,
    payment_id: str
) -> None:
    """
    Production-ready обработка успешного платежа.
    """
    try:
        # 1. Идемпотентность
        if payment_id and is_paid(payment_id):
            logger.info(f"Payment {payment_id} already processed, skipping.")
            return

        # 2. Проверка пользователя
        user = get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found for payment {payment_id}")
            return

        # 3. Парсинг дней
        try:
            days = int(plan)
        except ValueError:
            logger.error(f"Invalid plan: {plan}")
            return

        # 4. Активация пользователя
        updated_user = activate_paid(user_id, days)
        if not updated_user:
            logger.error(f"Failed to activate user {user_id}")
            return

        # 5. Синхронизация
        full_sync()
        restart_trusttunnel()

        # 6. Отправка карточки
        card = build_vpn_card(user_id)
        if card and "text" in card:
            try:
                await bot.send_message(
                    chat_id=int(user_id),
                    text=card["text"],
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
        else:
            logger.warning(f"Could not build card for user {user_id}")

        # 7. Помечаем платёж как обработанный
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"✅ Payment {payment_id} successfully processed for user {user_id} ({days} days)")

    except Exception as e:
        logger.exception(f"Critical error processing payment {payment_id}")