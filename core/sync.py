import os
import logging
from datetime import datetime
from filelock import FileLock

from core.db import load_users, save_users
from core.credentials import rebuild_credentials_from_db


LOCK_PATH = "/opt/trustsystem/storage/sync.lock"
os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)

lock = FileLock(LOCK_PATH, timeout=20)


def _safe_parse(dt: str):
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return None


def full_sync():
    with lock:
        users = load_users()

        now = datetime.utcnow()
        changed = False

        for u in users:
            exp = u.get("expires_at")

            # нет даты — пропускаем
            if not exp:
                continue

            exp_dt = _safe_parse(exp)
            if not exp_dt:
                logging.error(f"[SYNC] bad date: {exp}")
                continue

            # 🔥 EXPIRE
            if exp_dt < now:
                if u.get("status") != "inactive":
                    u["status"] = "inactive"
                    changed = True
                continue

            # 🔥 RE-ACTIVATE (ВАЖНО)
            if exp_dt > now:
                if u.get("status") != "active":
                    u["status"] = "active"
                    changed = True

        if changed:
            save_users(users)
            logging.info("[SYNC] users updated")

        # rebuild только если есть пользователи
        if users:
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