import asyncio
import logging
from datetime import datetime

from yookassa import Payment

from services.payment_service import load, save, is_paid
from services.control_plane import process_successful_payment

logger = logging.getLogger(__name__)

POLL = 10


async def worker_loop():

    while True:
        try:
            data = load()
            changed = False

            for p in data:
                try:
                    payment_id = p.get("id")

                    if p.get("status") == "paid":
                        continue

                    payment = Payment.find_one(payment_id)

                    tg_id = p.get("tg_id")
                    if not tg_id:
                        tg_id = (payment.metadata or {}).get("user_id")

                    if not tg_id:
                        continue

                    try:
                        tg_id = int(tg_id)
                    except:
                        continue

                    if payment.status == "succeeded":
                        if not is_paid(payment_id):
                            await process_successful_payment(
                                tg_id,
                                p.get("plan"),
                                payment_id
                            )

                        p["status"] = "paid"
                        p["paid_at"] = datetime.utcnow().isoformat()
                        changed = True

                    elif payment.status == "canceled":
                        p["status"] = "canceled"
                        changed = True

                except Exception as e:
                    logger.error(e)

            if changed:
                save(data)

            await asyncio.sleep(POLL)

        except Exception as e:
            logger.error(e)
            await asyncio.sleep(POLL)