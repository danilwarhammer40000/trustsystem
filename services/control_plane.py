import logging
from aiogram import Bot
from datetime import datetime

from config.settings import PUBLIC_BOT_TOKEN
from services.user_service import create_user, extend_user
from services.user_service import safe_int
from services.payment_service import is_paid, mark_paid
from services.vpn_card_builder import build_vpn_card
from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)

async def process_successful_payment(user_id, plan: str, payment_id: str = None):
    try:
        tg_id = safe_int(user_id)  # добавь safe_int из user_service или импортируй
        if not tg_id:
            logger.error(f"Invalid user_id: {user_id}")
            return

        if payment_id and is_paid(payment_id):
            logger.info(f"Payment {payment_id} already processed")
            return

        create_user(tg_id)  # ensure exists
        days = int(plan) if str(plan).isdigit() else 30

        updated = extend_user(tg_id, days)
        logger.info(f"Extended user {tg_id} for {days} days")

        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"Sync error: {e}")

        card = build_vpn_card(updated["username"])
        await bot.send_message(
            chat_id=tg_id,
            text=card.get("text", "Доступ выдан!"),
            parse_mode="HTML"
        )

        if payment_id:
            mark_paid(payment_id)

    except Exception as e:
        logger.exception(f"process_successful_payment error: {e}")