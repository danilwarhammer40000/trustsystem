import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# =========================
# PATH FIX (важно для systemd)
# =========================
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# =========================
# APP
# =========================
app = FastAPI(title="TrustSystem Webhook")

# =========================
# IMPORT ROUTERS
# =========================
from core.webhook.youkassa import router as yookassa_router  # noqa

app.include_router(yookassa_router)


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    uvicorn.run(
        "run_webhook:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )