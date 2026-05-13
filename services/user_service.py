import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional

STORAGE_PATH = "/opt/trustsystem/storage/users.json"
lock = threading.Lock()


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
# SAFE PARSE
# =========================

def safe_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except:
        return None


def safe_date(value: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value) if value else None
    except:
        return None


# =========================
# CORE GET
# =========================

def get_user_by_tg(tg_id: int) -> Optional[Dict]:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return None

    users = load_users()
    return next((u for u in users if safe_int(u.get("telegram_id")) == tg_id), None)


def get_all_users() -> List[Dict]:
    return load_users()


# =========================
# CREATE SAFE
# =========================

def create_user(tg_id: int) -> Dict:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        raise ValueError("invalid tg_id")

    users = load_users()

    existing = get_user_by_tg(tg_id)
    if existing:
        return existing

    user = {
        "telegram_id": tg_id,
        "username": f"user_{tg_id}",
        "password": "auto",
        "plan": "trial",
        "status": "active",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None,
    }

    users.append(user)
    save_users(users)
    return user


# =========================
# UPDATE SINGLE SOURCE
# =========================

def _update_user(user: Dict) -> Dict:
    users = load_users()

    tg_id = safe_int(user.get("telegram_id"))
    if tg_id is None:
        raise ValueError("missing tg_id")

    for i, u in enumerate(users):
        if safe_int(u.get("telegram_id")) == tg_id:
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
    user = create_user(tg_id)

    days = safe_int(days) or 0

    now = datetime.utcnow()
    exp = safe_date(user.get("expires_at"))

    if exp and exp > now:
        new_exp = exp + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["status"] = "active"

    return _update_user(user)


# =========================
# DELETE SAFE
# =========================

def delete_user(tg_id: int) -> bool:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return False

    users = load_users()
    new_users = [u for u in users if safe_int(u.get("telegram_id")) != tg_id]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True


def get_user_by_username(username: str):
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)