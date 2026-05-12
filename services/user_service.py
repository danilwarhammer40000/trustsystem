import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict

STORAGE_PATH = "/opt/trustsystem/storage/users.json"


# =========================
# LOW LEVEL
# =========================

def load_users() -> List[Dict]:
    if not os.path.exists(STORAGE_PATH):
        return []

    with open(STORAGE_PATH, "r") as f:
        return json.load(f)


def save_users(users: List[Dict]) -> None:
    with open(STORAGE_PATH, "w") as f:
        json.dump(users, f, indent=2)


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
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# =========================
# FINDERS
# =========================

def get_user_by_tg(telegram_id: int) -> Optional[Dict]:
    users = load_users()
    return next((u for u in users if u.get("telegram_id") == int(telegram_id)), None)


def get_user_by_username(username: str) -> Optional[Dict]:
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


def get_all_users() -> List[Dict]:
    return load_users()


# =========================
# CREATE (NEW)
# =========================

def create_user_if_not_exists(telegram_id: int) -> Dict:
    users = load_users()

    existing = get_user_by_tg(telegram_id)
    if existing:
        return existing

    # попытка "привязать" старого пользователя
    for u in users:
        if u.get("username") == f"user_{telegram_id}":
            u["telegram_id"] = int(telegram_id)
            save_users(users)
            return u

    now = datetime.utcnow()

    user = {
        "telegram_id": int(telegram_id),
        "username": f"user_{telegram_id}",
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
# CREATE (LEGACY)
# =========================

def create_user(username: str) -> Dict:
    users = load_users()

    existing = get_user_by_username(username)
    if existing:
        return existing

    now = datetime.utcnow()

    user = {
        "telegram_id": None,
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
# TRIAL
# =========================

def activate_trial(telegram_id: int, days: int = 3) -> Dict:
    user = create_user_if_not_exists(telegram_id)

    if user.get("trial_used"):
        return user

    now = datetime.utcnow()
    user["trial_used"] = True
    user["plan"] = "trial"
    user["expires_at"] = (now + timedelta(days=days)).isoformat()

    users = load_users()
    for i, u in enumerate(users):
        if u.get("username") == user["username"]:
            users[i] = user
            break

    save_users(users)
    return user


# =========================
# EXTEND (NEW)
# =========================

def extend_user_by_tg(telegram_id: int, days: int) -> Dict:
    user = create_user_if_not_exists(telegram_id)

    now = datetime.utcnow()
    current_expiry = safe_parse_date(user.get("expires_at"))

    if current_expiry and current_expiry > now:
        new_expiry = current_expiry + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)

    user["expires_at"] = new_expiry.isoformat()
    user["plan"] = f"{days}d"
    user["status"] = "active"

    users = load_users()
    for i, u in enumerate(users):
        if u.get("username") == user["username"]:
            users[i] = user
            break

    save_users(users)
    return user


# =========================
# EXTEND (LEGACY)
# =========================

def extend_user(username: str, days: int) -> Dict:
    user = get_user_by_username(username)
    if not user:
        raise ValueError("User not found")

    tg_id = user.get("telegram_id")

    if tg_id:
        return extend_user_by_tg(tg_id, days)

    # fallback
    now = datetime.utcnow()
    current_expiry = safe_parse_date(user.get("expires_at"))

    if current_expiry and current_expiry > now:
        new_expiry = current_expiry + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)

    user["expires_at"] = new_expiry.isoformat()
    user["plan"] = f"{days}d"
    user["status"] = "active"

    users = load_users()
    for i, u in enumerate(users):
        if u.get("username") == username:
            users[i] = user
            break

    save_users(users)
    return user


# =========================
# ADMIN UTILS
# =========================

def set_expire(username: str, expires_at: str) -> Dict:
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["expires_at"] = expires_at
            u["status"] = "active"
            save_users(users)
            return u

    raise ValueError("User not found")


# =========================
# DELETE
# =========================

def delete_user(username: str) -> bool:
    users = load_users()
    new_users = [u for u in users if u.get("username") != username]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True


def delete_user_by_tg(telegram_id: int) -> bool:
    users = load_users()
    new_users = [u for u in users if u.get("telegram_id") != int(telegram_id)]

    if len(new_users) == len(users):
        return False

    save_users(new_users)
    return True