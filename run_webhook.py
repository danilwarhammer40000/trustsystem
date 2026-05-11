import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

app = FastAPI(title="TrustSystem Webhook")

from core.webhook.yookassa import router as yookassa_router

app.include_router(yookassa_router)


if __name__ == "__main__":
    uvicorn.run(
        "run_webhook:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )