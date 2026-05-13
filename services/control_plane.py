import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN
from services.user_service import create_user, extend_user, safe_int
from services.payment_service import is_paid, mark_paid
from services.vpn_card_builder import build_vpn_card
from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)

async def process_successful_payment(user_id, plan: str, payment_id: str = None):
    try:
        tg_id = safe_int(user_id)
        if not tg_id:
            logger.error(f"Invalid user_id: {user_id}")
            return

        if payment_id and is_paid(payment_id):
            logger.info(f"Payment already processed: {payment_id}")
            return

        create_user(tg_id)
        days = int(plan) if str(plan).isdigit() else 30

        updated = extend_user(tg_id, days)
        logger.info(f"User {tg_id} extended for {days} days")

        full_sync()
        restart_trusttunnel()

        card = build_vpn_card(str(tg_id))
        await bot.send_message(
            chat_id=tg_id,
            text=card.get("text", "Доступ выдан!"),
            parse_mode="HTML"
        )

        if payment_id:
            mark_paid(payment_id)

    except Exception as e:
        logger.exception(f"process_successful_payment error: {e}")