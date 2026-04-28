import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")

ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0"))
