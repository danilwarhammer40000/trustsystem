import asyncio
import logging
from datetime import datetime, timedelta

from yookassa import Payment

from services.payment_service import load, save, is_paid
from services.control_plane import process_successful_payment

logger = logging.getLogger(__name__)

POLL_INTERVAL = 10
PAYMENT_TIMEOUT_MINUTES = 30


async def worker_loop():
    logger.info("🚀 Payment worker started")

    while True:
        try:
            data = load()
            updated = False

            for p in data:
                try:
                    payment_id = p.get("id")

                    # уже обработан
                    if p.get("status") == "paid":
                        continue

                    # timeout
                    created_at = p.get("created_at")
                    if created_at:
                        created_dt = datetime.fromisoformat(created_at)
                        if datetime.utcnow() - created_dt > timedelta(minutes=PAYMENT_TIMEOUT_MINUTES):
                            logger.info(f"[TIMEOUT] {payment_id}")
                            continue

                    # запрос в YooKassa
                    payment = Payment.find_one(payment_id)

                    if payment.status == "succeeded":
                        logger.info(f"[PAID] {payment_id}")

                        # 🔥 достаем tg_id
                        tg_id = p.get("tg_id")

                        # fallback из metadata (на случай старых записей)
                        if not tg_id:
                            metadata = payment.metadata or {}
                            tg_id = metadata.get("user_id")

                        if not tg_id:
                            logger.error(f"[NO TG_ID] payment={payment_id}")
                            continue

                        tg_id = int(tg_id)

                        # 🔥 обработка (идемпотентная)
                        if not is_paid(payment_id):
                            await process_successful_payment(
                                user_id=tg_id,
                                plan=p.get("plan"),
                                payment_id=payment_id
                            )

                        # фиксируем локально
                        p["status"] = "paid"
                        p["paid_at"] = datetime.utcnow().isoformat()
                        updated = True

                    elif payment.status == "canceled":
                        logger.info(f"[CANCELED] {payment_id}")
                        p["status"] = "canceled"
                        updated = True

                except Exception as e:
                    logger.error(f"[PAYMENT ERROR] {p}: {e}")

            if updated:
                save(data)

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.exception(f"[WORKER ERROR]: {e}")
            await asyncio.sleep(POLL_INTERVAL)