import asyncio
import logging
from datetime import datetime, timedelta

from services.payment_service import (
    get_pending_payments,
    check_payment_status
)

from services.control_plane import process_successful_payment

logger = logging.getLogger(__name__)


POLL_INTERVAL = 10  # секунд
PAYMENT_TIMEOUT_MINUTES = 30


async def worker_loop():
    logger.info("🚀 Payment worker started")

    while True:
        try:
            payments = get_pending_payments()

            if not payments:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            for payment in payments:
                try:
                    payment_id = payment.get("id")
                    tg_id = payment.get("tg_id")
                    plan = payment.get("plan")
                    created_at = payment.get("created_at")

                    # --- timeout check ---
                    if created_at:
                        created_dt = datetime.fromisoformat(created_at)
                        if datetime.utcnow() - created_dt > timedelta(minutes=PAYMENT_TIMEOUT_MINUTES):
                            logger.info(f"[TIMEOUT] payment {payment_id}")
                            continue

                    # --- проверка статуса ---
                    status = check_payment_status(payment_id)

                    if status == "paid":
                        logger.info(f"[PAID] {payment_id}")

                        await process_successful_payment(
                            user_id=str(tg_id),
                            plan=str(plan),
                            payment_id=payment_id
                        )

                    elif status == "canceled":
                        logger.info(f"[CANCELED] {payment_id}")

                except Exception as e:
                    logger.error(f"[PAYMENT ERROR] {payment}: {e}")

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.exception(f"[WORKER LOOP ERROR]: {e}")
            await asyncio.sleep(POLL_INTERVAL)