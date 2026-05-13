import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.settings import ADMIN_BOT_TOKEN

from bots.admin.middleware.access import AdminAccessMiddleware

# routers
from bots.admin.handlers import (
    start,
    stats,
    users,
    manage
)

from services.control_plane import sync_all_users


# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# BOT INIT
# =========================

bot = Bot(token=ADMIN_BOT_TOKEN)
dp = Dispatcher()


# =========================
# MIDDLEWARE
# =========================

dp.message.middleware(AdminAccessMiddleware())
dp.callback_query.middleware(AdminAccessMiddleware())


# =========================
# ROUTERS (SAFE IMPORT BINDING)
# =========================

ROUTERS = [
    start.router,
    stats.router,
    users.router,
    manage.router,
]

for r in ROUTERS:
    try:
        dp.include_router(r)
    except Exception as e:
        logger.exception(f"[ROUTER LOAD ERROR] {e}")


# =========================
# SYNC LOOP
# =========================

async def scheduler_loop():
    while True:
        try:
            logger.info("[SYNC] start")
            await asyncio.to_thread(sync_all_users)
            logger.info("[SYNC] done")

        except Exception as e:
            logger.exception(f"[SYNC ERROR] {e}")

        await asyncio.sleep(300)


# =========================
# MAIN
# =========================

async def main():
    logger.info("ADMIN BOT STARTED")

    # background task
    asyncio.create_task(scheduler_loop())

    try:
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"[BOT CRASH] {e}")

    finally:
        try:
            await bot.session.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())