import os
import logging
from datetime import datetime
from filelock import FileLock

from core.db import load_users, save_users
from core.credentials import rebuild_credentials_from_db


LOCK_PATH = "/opt/trustsystem/storage/sync.lock"
os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)

lock = FileLock(LOCK_PATH, timeout=20)


def full_sync():
    with lock:
        users = load_users()

        now = datetime.utcnow()
        changed = False

        for u in users:
            if u.get("status") != "active":
                continue

            exp = u.get("expires_at")
            if not exp:
                continue

            try:
                exp_dt = datetime.fromisoformat(exp)

                if exp_dt < now:
                    u["status"] = "inactive"
                    changed = True

            except Exception as e:
                logging.error(f"[SYNC] date parse error: {e}")

        if changed:
            save_users(users)
            logging.info("[SYNC] users updated")

        rebuild_credentials_from_db(users)
        logging.info("[SYNC] credentials rebuilt")


def restart_trusttunnel():
    import subprocess

    try:
        subprocess.Popen(
            ["systemctl", "restart", "trusttunnel.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        logging.error(f"[SYNC] restart error: {e}")