import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict

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
    except Exception:
        return []


def save_users(users: List[Dict]) -> None:
    with lock:
        tmp = STORAGE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

        os.replace(tmp, STORAGE_PATH)


# =========================
# HELPERS
# =========================

def safe_parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def generate_password(length: int = 12) -> str:
    import random, string
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def build_username(tg_id: int) -> str:
    return f"user_{tg_id}"


# =========================
# CORE FINDERS
# =========================

def get_user_by_tg(tg_id: int) -> Optional[Dict]:
    if tg_id is None:
        return None

    users = load_users()
    return next((u for u in users if u.get("telegram_id") == int(tg_id)), None)


def get_user_by_username(username: str) -> Optional[Dict]:
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


def get_all_users() -> List[Dict]:
    return load_users()


# =========================
# CORE CREATE / GET OR CREATE
# =========================

def create_user(tg_id: int) -> Dict:
    if tg_id is None:
        raise ValueError("tg_id is required")

    users = load_users()

    # 1. already exists
    existing = get_user_by_tg(tg_id)
    if existing:
        return existing

    username = build_username(tg_id)

    # 2. legacy restore
    for u in users:
        if u.get("username") == username and u.get("telegram_id") is None:
            u["telegram_id"] = int(tg_id)
            save_users(users)
            return u

    now = datetime.utcnow()

    user = {
        "telegram_id": int(tg_id),
        "username": username,
        "password": generate_password(),
        "plan": "trial",
        "status": "active",
        "trial_used": False,
        "created_at": now.isoformat(),
        "expires_at": None,
    }

    users.append(user)
    save_users(users)
    return user


# =========================
# UPDATE CORE (SAFE SINGLE SOURCE OF TRUTH)
# =========================

def _update_user(user: Dict) -> Dict:
    users = load_users()

    tg_id = user.get("telegram_id")
    if tg_id is None:
        raise ValueError("Cannot update user without telegram_id")

    for i, u in enumerate(users):
        if u.get("telegram_id") == tg_id:
            users[i] = user
            save_users(users)
            return user

    # fallback insert (rare recovery case)
    users.append(user)
    save_users(users)
    return user


# =========================
# TRIAL
# =========================

def activate_trial(tg_id: int, days: int = 3) -> Dict:
    user = create_user(tg_id)

    if user.get("trial_used"):
        return user

    now = datetime.utcnow()

    user["trial_used"] = True
    user["plan"] = "trial"
    user["expires_at"] = (now + timedelta(days=days)).isoformat()

    return _update_user(user)


# =========================
# EXTEND (MAIN LOGIC)
# =========================

def extend_user(tg_id: int, days: int) -> Dict:
    user = create_user(tg_id)

    now = datetime.utcnow()
    current_exp = safe_parse_date(user.get("expires_at"))

    if current_exp and current_exp > now:
        new_exp = current_exp + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    user["expires_at"] = new_exp.isoformat()
    user["plan"] = f"{days}d"
    user["status"] = "active"

    return _update_user(user)


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


# =========================
# LEGACY SUPPORT
# =========================

def get_user(username: str):
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)