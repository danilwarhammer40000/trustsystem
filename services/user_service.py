from datetime import datetime, timedelta
import secrets
import string
import re

from core.db import load_users, save_users
from core.sync import full_sync


# =========================
# HELPERS
# =========================

def _generate_password(length: int = 12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _validate_username(username: str):
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        raise ValueError("INVALID_USERNAME")


# =========================
# GETTERS
# =========================

def get_all_users():
    return load_users()


def get_user(username: str):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            return u

    return None


def get_user_by_tg(tg_id: int):
    users = load_users()

    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):
            return u

    return None


# =========================
# CREATE (FIXED)
# =========================

def create_user(username: str, tg_id: int | None = None):
    _validate_username(username)

    users = load_users()

    # проверка username (TG ИГНОРИРУЕМ)
    for u in users:
        if u.get("username") == username:
            raise ValueError("USERNAME_TAKEN")

    password = _generate_password()

    user = {
        "username": username,
        "password": password,
        "telegram_id": tg_id,  # может быть None
        "plan": "manual",
        "status": "inactive",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None
    }

    users.append(user)
    save_users(users)

    return user


# =========================
# EXTEND (ГЛАВНАЯ ЛОГИКА)
# =========================

def extend_user(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            now = datetime.utcnow()

            # бесконечность
            if days == 0:
                u["status"] = "active"
                u["expires_at"] = None

                save_users(users)
                full_sync()
                return u

            base = now

            # если активен — продлеваем от текущей даты
            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"])
                    if old > now:
                        base = old
                except Exception:
                    pass

            u["status"] = "active"
            u["expires_at"] = (base + timedelta(days=days)).isoformat()

            save_users(users)
            full_sync()
            return u

    raise ValueError("USER_NOT_FOUND")


# =========================
# MANUAL DATE
# =========================

def set_manual_expire(username: str, date_str: str):
    """
    date_str формат: YYYY-MM-DD
    """

    users = load_users()

    for u in users:
        if u.get("username") == username:
            try:
                dt = datetime.fromisoformat(date_str)
            except Exception:
                raise ValueError("INVALID_DATE_FORMAT")

            u["status"] = "active"
            u["expires_at"] = dt.isoformat()

            save_users(users)
            full_sync()
            return u

    raise ValueError("USER_NOT_FOUND")


# =========================
# DELETE
# =========================

def delete_user(username: str):
    users = load_users()

    users = [u for u in users if u.get("username") != username]

    save_users(users)
    full_sync()


# =========================
# DEACTIVATE
# =========================

def deactivate_user(username: str):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["status"] = "inactive"

    save_users(users)
    full_sync()