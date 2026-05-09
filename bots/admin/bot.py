import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.settings import ADMIN_BOT_TOKEN

from bots.admin.middleware.access import AdminAccessMiddleware
from bots.admin.handlers import start, stats, users, sync, manage

from services.control_plane import sync_all_users


# =========================
# LOGGING
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
    Безопасный фоновой sync:
    - не падает
    - использует control_plane (единая логика)
    """
    while True:
        try:
            await asyncio.to_thread(sync_all_users)
        except Exception as e:
            logging.error(f"[SYNC ERROR] {e}")

        await asyncio.sleep(300)  # каждые 5 минут


# =========================
# MAIN
# =========================

async def main():
    logging.info("ADMIN BOT STARTED")