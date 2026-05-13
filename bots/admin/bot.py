import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.settings import ADMIN_BOT_TOKEN
from bots.admin.handlers import router
from core.sync import full_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=ADMIN_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)

async def scheduler_loop():
    while True:
        try:
            logger.info("[SYNC] start")
            await asyncio.to_thread(full_sync)
            logger.info("[SYNC] done")
        except Exception as e:
            logger.exception(f"[SYNC ERROR] {e}")
        await asyncio.sleep(300)

async def main():
    logger.info("ADMIN BOT STARTED")
    asyncio.create_task(scheduler_loop())
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"[BOT CRASH] {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())