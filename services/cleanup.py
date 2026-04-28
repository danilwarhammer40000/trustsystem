
import time
from core.credentials import delete_expired

def run():
    while True:
        delete_expired()
        time.sleep(3600)  # каждый час