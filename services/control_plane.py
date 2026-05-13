import logging
from aiogram import Bot

from config.settings import PUBLIC_BOT_TOKEN

from services.user_service import (
    create_user,
    extend_user,
    set_user_field
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
        updated = extend_user(tg_id, int(plan))

        set_user_field(tg_id, "trial_used", True)

        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"sync error {e}")

        card = build_vpn_card(updated["username"])

        await bot.send_message(
            chat_id=tg_id,
            text=card["text"],
            parse_mode="HTML"
        )

        mark_paid(payment_id)

    except Exception:
        logger.exception(f"[PAYMENT ERROR] {payment_id}")


def sync_all_users():
    try:
        full_sync()
        restart_trusttunnel()
    except Exception as e:
        logger.error(e)