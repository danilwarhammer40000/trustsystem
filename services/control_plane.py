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

        # 2. USER (через TG!)
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
            logger.error(f"sync error: {e}")

        # 6. VPN
        card = build_vpn_card(username)

        await bot.send_message(
            chat_id=int(user_id),
            text=card["text"],
            parse_mode="HTML"
        )

        # 7. mark paid
        if payment_id:
            mark_paid(payment_id)

        logger.info(f"[SUCCESS] payment done {payment_id}")

    except Exception as e:
        logger.exception(f"[CRITICAL] {payment_id}")