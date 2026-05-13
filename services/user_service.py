import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional

STORAGE_PATH = "/opt/trustsystem/storage/users.json"
lock = threading.Lock()


# =========================
# SAFE CAST
# =========================

def safe_tg_id(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except:
        return None


# =========================
# STORAGE
# =========================

def load_users() -> List[Dict]:
    if not os.path.exists(STORAGE_PATH):
        return []

    try:
        with open(STORAGE_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []


def save_users(users: List[Dict]) -> None:
    with lock:
        tmp = STORAGE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        os.replace(tmp, STORAGE_PATH)


# =========================
# FINDERS (SAFE)
# =========================

def get_all_users():
    return load_users()


def get_user_by_tg(tg_id):
    tg_id = safe_tg_id(tg_id)
    if tg_id is None:
        return None

    users = load_users()
    return next((u for u in users if safe_tg_id(u.get("telegram_id")) == tg_id), None)


def get_user_by_username(username: str):
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


# =========================
# CREATE
# =========================

def create_user(tg_id: int) -> Dict:
    tg_id = safe_tg_id(tg_id)
    if tg_id is None:
        raise ValueError("tg_id required")

    users = load_users()

    existing = get_user_by_tg(tg_id)
    if existing:
        return existing

    user = {
        "telegram_id": tg_id,
        "username": f"user_{tg_id}",
        "password": _password(),
        "plan": "trial",
        "status": "active",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None,
    }

    users.append(user)
    save_users(users)
    return user


def _password():
    import random, string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))


# =========================
# UPDATE CORE
# =========================

def _write(users, user):
    tg_id = safe_tg_id(user.get("telegram_id"))

    for i, u in enumerate(users):
        if safe_tg_id(u.get("telegram_id")) == tg_id:
            users[i] = user
            save_users(users)
            return user

    users.append(user)
    save_users(users)
    return user


# =========================
# EXTEND
# =========================

def extend_user(tg_id: int, days: int) -> Dict:
    tg_id = safe_tg_id(tg_id)
    if tg_id is None:
        raise ValueError("invalid tg_id")

    users = load_users()
    user = get_user_by_tg(tg_id)

    if not user:
        user = create_user(tg_id)
        users = load_users()

    now = datetime.utcnow()

    try:
        current = datetime.fromisoformat(user["expires_at"]) if user.get("expires_at") else None
    except:
        current = None

    if current and current > now:
        new_exp = current + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["status"] = "active"
    user["plan"] = f"{days}d"

    return _write(users, user)


# =========================
# SETTERS
# =========================

def set_expire(username: str, iso: str):
    users = load_users()
    user = get_user_by_username(username)

    if not user:
        raise ValueError("not found")

    user["expires_at"] = iso
    return _write(users, user)


def set_user_field(tg_id, field, value):
    tg_id = safe_tg_id(tg_id)
    if tg_id is None:
        return None

    users = load_users()
    user = get_user_by_tg(tg_id)

    if not user:
        return None

    user[field] = value
    return _write(users, user)


# =========================
# DELETE
# =========================

def delete_user(tg_id):
    tg_id = safe_tg_id(tg_id)
    if tg_id is None:
        return False

    users = load_users()
    new_users = [u for u in users if safe_tg_id(u.get("telegram_id")) != tg_id]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True