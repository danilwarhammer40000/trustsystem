import os
import subprocess
from datetime import datetime

from filelock import FileLock

from core.db import load_users, save_users
from core.credentials import rebuild_credentials_from_db


LOCK_PATH = "/opt/trustsystem/storage/sync.lock"
TRUSTTUNNEL_SERVICE = "trusttunnel.service"

# гарантируем что папка существует
os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)

lock = FileLock(LOCK_PATH, timeout=20)


def restart_trusttunnel():
    result = subprocess.run(
        ["systemctl", "restart", TRUSTTUNNEL_SERVICE],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)


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
            except:
                continue

        if changed:
            save_users(users)

        rebuild_credentials_from_db(users)
        restart_trusttunnel()
