import os

# ======================
# TOKENS
# ======================

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
PUBLIC_BOT_TOKEN = os.getenv("PUBLIC_BOT_TOKEN")

# ======================
# GENERAL SETTINGS
# ======================

DOMAIN = os.getenv("DOMAIN")

# ADMIN TG ID (fallback = 0 если не задан)
ADMIN_TG_ID_RAW = os.getenv("ADMIN_TG_ID", "0")

try:
    ADMIN_TG_ID = int(ADMIN_TG_ID_RAW)
except ValueError:
    raise ValueError(f"ADMIN_TG_ID must be int, got: {ADMIN_TG_ID_RAW}")

# ======================
# VALIDATION
# ======================

if not ADMIN_BOT_TOKEN:
    raise RuntimeError("ADMIN_BOT_TOKEN is missing in environment")

if not PUBLIC_BOT_TOKEN:
    raise RuntimeError("PUBLIC_BOT_TOKEN is missing in environment")

if ":" not in ADMIN_BOT_TOKEN:
    raise ValueError("ADMIN_BOT_TOKEN format is invalid")

if ":" not in PUBLIC_BOT_TOKEN:
    raise ValueError("PUBLIC_BOT_TOKEN format is invalid")
