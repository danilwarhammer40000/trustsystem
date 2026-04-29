import asyncio

from aiogram import Bot, Dispatcher

from config.settings import ADMIN_BOT_TOKEN
from bots.admin.middleware.access import AdminAccessMiddleware

from bots.admin.handlers import users, sync, stats

bot = Bot(token=ADMIN_BOT_TOKEN)
dp = Dispatcher()

# 🔐 GLOBAL SECURITY MIDDLEWARE
dp.message.middleware(AdminAccessMiddleware())
dp.callback_query.middleware(AdminAccessMiddleware())

# routers
dp.include_router(users.router)
dp.include_router(sync.router)
dp.include_router(stats.router)


from core.scheduler import periodic_sync


async def main():
    print("ADMIN BOT STARTED")

    asyncio.create_task(periodic_sync())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
