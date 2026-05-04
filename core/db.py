import json
import os
import tempfile
from typing import List, Dict
from filelock import FileLock

DB_PATH = "/opt/trustsystem/storage/users.json"
LOCK_PATH = "/opt/trustsystem/storage/db.lock"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

lock = FileLock(LOCK_PATH, timeout=10)


# =========================
# INIT SAFE FILE
# =========================
def _ensure():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


# =========================
# SAFE LOAD (CRASH PROOF)
# =========================
def load_users() -> List[Dict]:
    with lock:
        _ensure()

        try:
            with open(DB_PATH, "r") as f:
                data = json.load(f)

                if not isinstance(data, list):
                    return []

                return data

        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            # recovery mode
            return []


# =========================
# SAFE SAVE (ATOMIC WRITE)
# =========================
def save_users(data: List[Dict]):
    with lock:
        _ensure()

        tmp_dir = os.path.dirname(DB_PATH)

        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=tmp_dir
        ) as tmp:

            json.dump(
                data,
                tmp,
                indent=2,
                ensure_ascii=False
            )

            tmp_path = tmp.name

        # atomic replace (no corruption possible)
        os.replace(tmp_path, DB_PATH)