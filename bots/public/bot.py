import asyncio

from aiogram import Bot, Dispatcher

from config.settings import PUBLIC_BOT_TOKEN

from bots.public.handlers import (
    start,
    connect,
    username,
    profile,
    extend,
    payments
)

bot = Bot(token=PUBLIC_BOT_TOKEN)
dp = Dispatcher()

# порядок важен (FSM → ниже по стеку)
dp.include_router(start.router)
dp.include_router(connect.router)
dp.include_router(username.router)
dp.include_router(extend.router)
dp.include_router(profile.router)
dp.include_router(payments.router)


async def main():
    print("PUBLIC BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
