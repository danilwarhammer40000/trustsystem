import os
from dotenv import load_dotenv

load_dotenv()


# ======================
# SAFE ENV LOADER
# ======================

def env(name: str, default=None, required=False, cast=None):
    value = os.getenv(name)

    if value is None or value == "":
        if required:
            raise RuntimeError(f"{name} missing")
        return default

    if cast:
        try:
            return cast(value)
        except Exception:
            raise RuntimeError(f"{name} invalid format")

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


# ======================
# ADMIN SETTINGS
# ======================

ADMIN_TG_ID = env("ADMIN_TG_ID", default="0", cast=int)


# ======================
# YOOKASSA
# ======================

YOOKASSA_SHOP_ID = env("YOOKASSA_SHOP_ID", default="")
YOOKASSA_API_KEY = env("YOOKASSA_API_KEY", default="")


# ======================
# VALIDATION (STRICT ONLY FOR TOKENS)
# ======================

if ":" not in ADMIN_BOT_TOKEN:
    raise RuntimeError("ADMIN_BOT_TOKEN invalid format")

if ":" not in PUBLIC_BOT_TOKEN:
    raise RuntimeError("PUBLIC_BOT_TOKEN invalid format")