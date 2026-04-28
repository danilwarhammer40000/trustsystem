import subprocess
from filelock import FileLock

from core.db import load_users
from core.credentials import rebuild_credentials_from_db

LOCK_PATH = "/opt/trustsystem/storage/sync.lock"
TRUSTTUNNEL_SERVICE = "trusttunnel.service"

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
        rebuild_credentials_from_db(users)
        restart_trusttunnel()
