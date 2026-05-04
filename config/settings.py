import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
PUBLIC_BOT_TOKEN = os.getenv("PUBLIC_BOT_TOKEN")

DOMAIN = os.getenv("DOMAIN", "")

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0"))

# ✅ YooKassa
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY", "")

if not ADMIN_BOT_TOKEN:
    raise RuntimeError("ADMIN_BOT_TOKEN missing")

if not PUBLIC_BOT_TOKEN:
    raise RuntimeError("PUBLIC_BOT_TOKEN missing")