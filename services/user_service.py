import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional

STORAGE_PATH = "/opt/trustsystem/storage/users.json"
lock = threading.Lock()

def load_users() -> List[Dict]:
    if not os.path.exists(STORAGE_PATH):
        return []
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_users(users: List[Dict]) -> None:
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    with lock:
        tmp = STORAGE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        os.replace(tmp, STORAGE_PATH)

def safe_int(value) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def safe_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except:
        return None

def get_user_by_tg(tg_id) -> Optional[Dict]:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return None
    users = load_users()
    for u in users:
        if safe_int(u.get("telegram_id")) == tg_id:
            return u
    return None

def get_all_users() -> List[Dict]:
    return load_users()

def create_user(tg_id) -> Dict:   # только позиционный/один аргумент
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

def extend_user(tg_id: int, days: int) -> Dict:
    user = create_user(tg_id)  # dict

    days = safe_int(days) or 0
    now = datetime.utcnow()
    exp = safe_date(user.get("expires_at"))

    if exp and exp > now:
        new_exp = exp + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["status"] = "active"

    # обновляем
    users = load_users()
    tg = safe_int(user["telegram_id"])
    for i, u in enumerate(users):
        if safe_int(u.get("telegram_id")) == tg:
            users[i] = user
            break
    else:
        users.append(user)
    save_users(users)
    return user

def delete_user(tg_id) -> bool:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return False

    users = load_users()
    new_users = [u for u in users if safe_int(u.get("telegram_id")) != tg_id]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True

def activate_trial(tg_id):
    user = create_user(tg_id)
    if user.get("trial_used"):
        raise ValueError("Trial already used")
    user["trial_used"] = True
    user["expires_at"] = (datetime.utcnow() + timedelta(days=3)).isoformat()
    # обновить в файле (через extend_user логику или напрямую)
    extend_user(tg_id, 0)  # просто чтобы сохранить флаги
    return user