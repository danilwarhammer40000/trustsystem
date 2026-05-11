import sys
from pathlib import Path
import logging
import uvicorn
from fastapi import FastAPI

# ====================== НАСТРОЙКА ЛОГИРОВАНИЯ ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# ====================== ПУТИ ======================
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# ====================== FASTAPI ======================
app = FastAPI(
    title="TrustSystem Webhook",
    description="YooKassa Webhook Handler",
    version="1.0.0"
)

# ====================== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ======================
from core.webhook.yookassa import router as yookassa_router

app.include_router(yookassa_router)

# ====================== ЗАПУСК ======================
def main():
    logger.info("🚀 Starting TrustSystem Webhook server on port 8000...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,           # В продакшене обязательно False
        log_level="info",
        workers=1,              # Для webhook лучше 1 worker + background tasks
        timeout_keep_alive=65,
    )


if __name__ == "__main__":
    main()