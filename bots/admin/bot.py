import asyncio

from aiogram import Bot, Dispatcher

from config.settings import ADMIN_BOT_TOKEN

from bots.admin.middleware.access import AdminAccessMiddleware
from bots.admin.handlers import start, stats, users, sync, manage

from core.scheduler import periodic_sync


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
# MAIN LOOP
# =========================

async def main():
    print("ADMIN BOT STARTED")

    try:
        asyncio.create_task(periodic_sync())
    except Exception as e:
        print(f"[SCHEDULER ERROR] {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())