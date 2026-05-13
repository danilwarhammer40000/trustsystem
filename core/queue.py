import json
import os
import time
from filelock import FileLock

QUEUE_FILE = "/opt/trustsystem/storage/queue.json"
LOCK_FILE = "/opt/trustsystem/storage/queue.lock"

os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)

lock = FileLock(LOCK_FILE, timeout=10)


def _read():
    if not os.path.exists(QUEUE_FILE):
        return []

    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _write(data):
    tmp = QUEUE_FILE + ".tmp"

    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(tmp, QUEUE_FILE)


def push(task: dict):
    with lock:
        data = _read()
        data.append({
            "task": task,
            "retries": 0,
            "created_at": time.time()
        })
        _write(data)


def pop():
    with lock:
        data = _read()
        if not data:
            return None

        item = data.pop(0)
        _write(data)
        return item


def requeue(item):
    with lock:
        item["retries"] += 1

        # 🔥 защита от бесконечного цикла
        if item["retries"] > 5:
            return

        data = _read()
        data.append(item)
        _write(data)