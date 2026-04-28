import subprocess
from filelock import FileLock

from core.repository import users_repo
from core.credentials import rebuild_credentials_from_db

LOCK_PATH = "/opt/trusttunnel/sync.lock"
TRUSTTUNNEL_SERVICE = "trusttunnel.service"

lock = FileLock(LOCK_PATH, timeout=20)


def restart_trusttunnel():
    result = subprocess.run(
        ["systemctl", "restart", TRUSTTUNNEL_SERVICE],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"trusttunnel restart failed: {result.stderr}")


def full_sync():
    with lock:
        users = users_repo.get_all()
        rebuild_credentials_from_db(users)
        restart_trusttunnel()