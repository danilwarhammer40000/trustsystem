import json
import os
import tempfile
from typing import List, Dict
from filelock import FileLock

DB_PATH = "/opt/trustsystem/storage/users.json"
LOCK_PATH = "/opt/trustsystem/storage/db.lock"

# гарантируем директорию ДО создания lock
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

lock = FileLock(LOCK_PATH, timeout=10)


def _ensure():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


def load_users() -> List[Dict]:
    with lock:
        _ensure()
        with open(DB_PATH, "r") as f:
            return json.load(f)


def save_users(data: List[Dict]):
    with lock:
        _ensure()

        tmp_dir = os.path.dirname(DB_PATH)

        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=tmp_dir
        ) as tmp:

            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name

        os.replace(tmp_path, DB_PATH)
