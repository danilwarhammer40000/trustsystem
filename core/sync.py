import os
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
                if datetime.fromisoformat(exp) < now:
                    u["status"] = "inactive"
                    changed = True
            except:
                continue

        if changed:
            save_users(users)

        rebuild_credentials_from_db(users)


def restart_trusttunnel():
    import subprocess

    subprocess.Popen(
        ["systemctl", "restart", "trusttunnel.service"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )