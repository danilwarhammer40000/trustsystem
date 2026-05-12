import asyncio
from workers.payment_worker import worker_loop

asyncio.run(worker_loop())