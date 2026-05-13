from datetime import datetime
import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user,
    extend_user,
)

from services.payment_service import is_paid, mark_paid
from services.vpn_card_builder import build_vpn_card
from core.sync import full_sync, restart_trusttunnel

logger = logging.getLogger(__name__)
bot = Bot(token=PUBLIC_BOT_TOKEN)


async def process_successful_payment(user_id: int, plan: str, payment_id: str):
    try:
        tg_id = int(user_id)

        if payment_id and is_paid(payment_id):
            return

        user = create_user(tg_id)

        days = int(plan) if str(plan).isdigit() else 0
        if days <= 0:
            logger.error(f"[BAD PLAN] {plan}")
            return

        updated = extend_user(tg_id, days)
        username = updated["username"]

        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(e)

        card = build_vpn_card(username)

        await bot.send_message(
            chat_id=tg_id,
            text=card["text"],
            parse_mode="HTML"
        )

        if payment_id:
            mark_paid(payment_id)

    except Exception as e:
        logger.exception(e)