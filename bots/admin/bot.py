import asyncio
from aiogram import Bot, Dispatcher
from config.settings import ADMIN_TOKEN

bot = Bot(token=ADMIN_TOKEN)
dp = Dispatcher()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
