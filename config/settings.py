import os

# ======================
# TOKENS
# ======================

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
PUBLIC_BOT_TOKEN = os.getenv("PUBLIC_BOT_TOKEN")

# ======================
# GENERAL SETTINGS
# ======================

DOMAIN = os.getenv("DOMAIN", "")

# ======================
# ADMIN TG ID (SAFE PARSE)
# ======================

ADMIN_TG_ID_RAW = os.getenv("ADMIN_TG_ID")

def _parse_admin_id(value):
    if value is None:
        return 0

    value = value.strip()

    if value == "":
        return 0

    try:
        return int(value)
    except ValueError:
        print(f"[WARNING] ADMIN_TG_ID invalid: {value}, fallback to 0")
        return 0

ADMIN_TG_ID = _parse_admin_id(ADMIN_TG_ID_RAW)

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


# ======================
# PAYMENTS
# ======================

YOOMONEY_RECEIVER = os.getenv("YOOMONEY_RECEIVER")
YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN", "")