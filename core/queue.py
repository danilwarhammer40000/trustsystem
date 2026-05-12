import json
import os
import threading

FILE = "storage/queue.json"
lock = threading.Lock()


def load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return []


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


def push(task: dict):
    with lock:
        data = load()
        data.append(task)
        save(data)


def pop():
    with lock:
        data = load()
        if not data:
            return None
        task = data.pop(0)
        save(data)
        return task