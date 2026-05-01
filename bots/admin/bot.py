import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.settings import ADMIN_BOT_TOKEN

from bots.admin.middleware.access import AdminAccessMiddleware
from bots.admin.handlers import start, stats, users, sync, manage

from core.scheduler import periodic_sync


# =========================
# LOGGING (ВАЖНО)
# =========================

logging.basicConfig(level=logging.INFO)


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
# ROUTERS
# =========================

dp.include_router(start.router)
dp.include_router(stats.router)
dp.include_router(users.router)
dp.include_router(sync.router)
dp.include_router(manage.router)


# =========================
# SAFE SCHEDULER
# =========================

async def scheduler_loop():
    """
    Защищённый фоновой цикл sync.
    Никогда не падает и не убивает бот.
    """
    while True:
        try:
            await asyncio.to_thread(periodic_sync)
        except Exception as e:
            logging.error(f"[SYNC ERROR] {e}")

        await asyncio.sleep(300)  # каждые 5 минут


# =========================
# MAIN LOOP
# =========================

async def main():
    print("ADMIN BOT STARTED")

    # scheduler НЕ должен ломать bot
    asyncio.create_task(scheduler_loop())

    await dp.start_polling(bot)


# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":
    asyncio.run(main())