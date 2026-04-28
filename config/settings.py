import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
PUBLIC_TOKEN = os.getenv("PUBLIC_TOKEN")
