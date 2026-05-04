import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config.settings import PUBLIC_BOT_TOKEN

from bots.public.handlers import start, connect, payments, profile, cancel

redis = Redis(host="localhost", port=6379)
storage = RedisStorage(redis)

bot = Bot(token=PUBLIC_BOT_TOKEN)
dp = Dispatcher(storage=storage)

# регистрация роутеров
dp.include_router(start.router)
dp.include_router(connect.router)
dp.include_router(payments.router)
dp.include_router(profile.router)
dp.include_router(cancel.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())