import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.settings import PUBLIC_BOT_TOKEN
from bots.public.handlers import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=PUBLIC_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    print("PUBLIC BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())