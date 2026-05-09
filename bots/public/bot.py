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
    profile,
    cancel,
    extend_menu
)


# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)


# =========================
# REDIS / FSM
# =========================

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

storage = RedisStorage(redis)


# =========================
# BOT INIT
# =========================

bot = Bot(token=PUBLIC_BOT_TOKEN)
dp = Dispatcher(storage=storage)


# =========================
# ROUTERS (FIXED ORDER)
# =========================

dp.include_router(start.router)
dp.include_router(connect.router)
dp.include_router(extend_menu.router)
dp.include_router(profile.router)
dp.include_router(cancel.router)


# =========================
# MAIN
# =========================

async def main():
    logging.info("PUBLIC BOT STARTED")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(f"[BOT ERROR] {e}")
    finally:
        await bot.session.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())