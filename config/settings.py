import os
from dotenv import load_dotenv

load_dotenv()

def env(name: str, default=None, required: bool = False):
    value = os.getenv(name, default)

    if required and (value is None or value == ""):
        raise RuntimeError(f"{name} missing")

    return value


# ======================
# TOKENS
# ======================

ADMIN_BOT_TOKEN = env("ADMIN_BOT_TOKEN", required=True)
PUBLIC_BOT_TOKEN = env("PUBLIC_BOT_TOKEN", required=True)

# ======================
# GENERAL SETTINGS
# ======================

DOMAIN = env("DOMAIN", default="")

# safe parse int
ADMIN_TG_ID_RAW = env("ADMIN_TG_ID", default="0")
try:
    ADMIN_TG_ID = int(ADMIN_TG_ID_RAW) if ADMIN_TG_ID_RAW else 0
except:
    ADMIN_TG_ID = 0


# ======================
# YOOKASSA (optional)
# ======================

YOOKASSA_SHOP_ID = env("YOOKASSA_SHOP_ID", default="")
YOOKASSA_API_KEY = env("YOOKASSA_API_KEY", default="")

# ======================
# VALIDATION (soft)
# ======================

if ":" not in ADMIN_BOT_TOKEN:
    raise RuntimeError("ADMIN_BOT_TOKEN invalid")

if ":" not in PUBLIC_BOT_TOKEN:
    raise RuntimeError("PUBLIC_BOT_TOKEN invalid")