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
# SAFE HELPERS
# =========================

def safe_dt(value: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value) if value else None
    except:
        return None


def get_all_users() -> List[Dict]:
    return load_users()


def get_user_by_tg(tg_id: int) -> Optional[Dict]:
    if tg_id is None:
        return None
    users = load_users()
    return next((u for u in users if u.get("telegram_id") == int(tg_id)), None)


def get_user_by_username(username: str) -> Optional[Dict]:
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


# =========================
# CREATE
# =========================

def create_user(tg_id: int) -> Dict:
    if tg_id is None:
        raise ValueError("tg_id required")

    users = load_users()

    existing = get_user_by_tg(tg_id)
    if existing:
        return existing

    username = f"user_{tg_id}"

    now = datetime.utcnow()

    user = {
        "telegram_id": int(tg_id),
        "username": username,
        "password": _gen_password(),
        "plan": "trial",
        "status": "active",
        "trial_used": False,
        "created_at": now.isoformat(),
        "expires_at": None
    }

    users.append(user)
    save_users(users)
    return user


def _gen_password(length: int = 12) -> str:
    import random, string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


# =========================
# UPDATE CORE (ONLY SOURCE OF TRUTH)
# =========================

def _write(users: List[Dict], user: Dict) -> Dict:
    tg_id = user.get("telegram_id")

    for i, u in enumerate(users):
        if u.get("telegram_id") == tg_id:
            users[i] = user
            save_users(users)
            return user

    users.append(user)
    save_users(users)
    return user


# =========================
# EXTEND LOGIC
# =========================

def extend_user(tg_id: int, days: int) -> Dict:
    users = load_users()
    user = get_user_by_tg(tg_id)

    if not user:
        user = create_user(tg_id)
        users = load_users()

    now = datetime.utcnow()
    current = safe_dt(user.get("expires_at"))

    if current and current > now:
        new_exp = current + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["status"] = "active"
    user["plan"] = f"{days}d"

    return _write(users, user)


def set_expire(username: str, iso_date: str) -> Dict:
    users = load_users()
    user = get_user_by_username(username)

    if not user:
        raise ValueError("user not found")

    user["expires_at"] = iso_date
    user["status"] = "active"

    return _write(users, user)


def set_user_field(tg_id: int, field: str, value) -> Dict:
    users = load_users()
    user = get_user_by_tg(tg_id)

    if not user:
        raise ValueError("user not found")

    user[field] = value
    return _write(users, user)


# =========================
# DELETE
# =========================

def delete_user(tg_id: int) -> bool:
    users = load_users()
    new_users = [u for u in users if u.get("telegram_id") != int(tg_id)]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True