import asyncio
from core.sync import full_sync


async def periodic_sync():
    while True:
        try:
            full_sync()
        except Exception as e:
            print("[AUTO SYNC ERROR]", str(e))

        await asyncio.sleep(3600)  # 1 час
