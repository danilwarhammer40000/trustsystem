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

def save_users(users: List[Dict]):
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    with lock:
        tmp = STORAGE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        os.replace(tmp, STORAGE_PATH)

def safe_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except:
        return None

def get_user_by_tg(tg_id) -> Optional[Dict]:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return None
    for u in load_users():
        if safe_int(u.get("telegram_id")) == tg_id:
            return u
    return None

def get_all_users() -> List[Dict]:
    return load_users()

def create_user(tg_id) -> Dict:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        raise ValueError("Invalid tg_id")

    users = load_users()
    if any(safe_int(u.get("telegram_id")) == tg_id for u in users):
        return get_user_by_tg(tg_id)

    user = {
        "telegram_id": tg_id,
        "username": f"user_{tg_id}",
        "password": "auto",
        "status": "active",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=3)).isoformat(),
    }
    users.append(user)
    save_users(users)
    return user

def extend_user(tg_id: int, days: int = 30) -> Dict:
    user = create_user(tg_id)
    now = datetime.utcnow()
    exp = None
    if user.get("expires_at"):
        try:
            exp = datetime.fromisoformat(user["expires_at"].replace("Z", "+00:00"))
        except:
            pass

    new_exp = max(exp, now) + timedelta(days=days) if exp else now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["status"] = "active"

    # update
    users = load_users()
    for i, u in enumerate(users):
        if safe_int(u.get("telegram_id")) == tg_id:
            users[i] = user
            break
    save_users(users)
    return user

def delete_user(tg_id) -> bool:
    tg_id = safe_int(tg_id)
    if tg_id is None:
        return False
    users = [u for u in load_users() if safe_int(u.get("telegram_id")) != tg_id]
    save_users(users)
    return True

def activate_trial(tg_id):
    user = get_user_by_tg(tg_id)
    if user and user.get("trial_used"):
        raise ValueError("Trial already used")
    user = create_user(tg_id)
    user["trial_used"] = True
    user["expires_at"] = (datetime.utcnow() + timedelta(days=3)).isoformat()
    # save
    users = load_users()
    for i, u in enumerate(users):
        if safe_int(u.get("telegram_id")) == tg_id:
            users[i] = user
            break
    save_users(users)
    return user