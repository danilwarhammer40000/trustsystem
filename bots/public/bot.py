import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config.settings import PUBLIC_BOT_TOKEN

# handlers
from bots.public.handlers import (
    start,
    connect,
    payments,
    profile,
    cancel
)


# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)


# =========================
# REDIS / FSM
# =========================

redis = Redis(host="localhost", port=6379, decode_responses=True)
storage = RedisStorage(redis)


# =========================
# BOT INIT
# =========================

bot = Bot(token=PUBLIC_BOT_TOKEN)
dp = Dispatcher(storage=storage)


# =========================
# ROUTERS
# =========================

dp.include_router(start.router)
dp.include_router(connect.router)
dp.include_router(payments.router)
dp.include_router(profile.router)
dp.include_router(cancel.router)


# =========================
# MAIN
# =========================

async def main():
    logging.info("PUBLIC BOT STARTED")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())