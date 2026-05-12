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
# CREATE
# =========================

def create_user_if_not_exists(telegram_id: int) -> Dict:
    users = load_users()

    existing = get_user_by_tg(telegram_id)
    if existing:
        return existing

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
# TRIAL
# =========================

def activate_trial(telegram_id: int, days: int = 3) -> Dict:
    users = load_users()

    for u in users:
        if u.get("telegram_id") == int(telegram_id):

            if u.get("trial_used"):
                return u

            now = datetime.utcnow()
            u["plan"] = "trial"
            u["trial_used"] = True
            u["expires_at"] = (now + timedelta(days=days)).isoformat()

            save_users(users)
            return u

    raise ValueError("User not found")


# =========================
# EXTEND (MAIN LOGIC)
# =========================

def extend_user_by_tg(telegram_id: int, days: int) -> Dict:
    users = load_users()

    for u in users:
        if u.get("telegram_id") == int(telegram_id):

            now = datetime.utcnow()

            current_expiry = u.get("expires_at")

            if current_expiry:
                current_expiry_dt = datetime.fromisoformat(current_expiry)

                if current_expiry_dt > now:
                    new_expiry = current_expiry_dt + timedelta(days=days)
                else:
                    new_expiry = now + timedelta(days=days)
            else:
                new_expiry = now + timedelta(days=days)

            u["expires_at"] = new_expiry.isoformat()
            u["plan"] = f"{days}d"
            u["status"] = "active"

            save_users(users)
            return u

    raise ValueError("User not found")


# =========================
# LEGACY EXTEND (BACKWARD COMPAT)
# =========================

def extend_user(username: str, days: int) -> Dict:
    user = get_user_by_username(username)
    if not user:
        raise ValueError("User not found")

    return extend_user_by_tg(user["telegram_id"], days)


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


# =========================
# UTILS
# =========================

def generate_password(length: int = 12) -> str:
    import random
    import string

    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))