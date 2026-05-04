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
    for u in load_users():
        if u.get("username") == username:
            return u
    return None

# =========================
# CREATE (UPDATED)
# =========================

def create_user(
    username: str,
    password: str | None = None,
    tg_id: int | None = None
):
    _validate_username(username)

    users = load_users()

    # проверка username
    for u in users:
        if u.get("username") == username:
            raise ValueError("USERNAME_TAKEN")

    # проверка telegram_id (если передан)
    if tg_id is not None:
        for u in users:
            if u.get("telegram_id") == tg_id:
                raise ValueError("TELEGRAM_ALREADY_LINKED")

    # генерация пароля
    password = password if password and password != "-" else _generate_password()

    user = {
        "username": username,
        "password": password,
        "telegram_id": tg_id,  # теперь сохраняем
        "plan": "trial" if tg_id else "manual",
        "status": "inactive",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None
    }

    users.append(user)
    save_users(users)

    full_sync()

    return user

# =========================
# EXTEND
# =========================

def extend_user(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            now = datetime.utcnow()

            # FIX ∞
            if days == 0:
                u["status"] = "active"
                u["expires_at"] = "2099-12-31T23:59:59"

                save_users(users)
                full_sync()
                return u

            base = now

            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"])
                    if old > now:
                        base = old
                except:
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

def set_expire(username: str, dt: datetime):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["expires_at"] = dt.isoformat()
            u["status"] = "active" if dt > datetime.utcnow() else "inactive"

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
# ACTIVATE TRIAL
# =========================

def activate_trial(username: str):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            if u.get("trial_used"):
                raise ValueError("TRIAL_ALREADY_USED")

            u["trial_used"] = True
            u["plan"] = "trial"

            save_users(users)

            return extend_user(username, 3)

    raise ValueError("USER_NOT_FOUND")


# =========================
# ACTIVATE PAID
# =========================

def activate_paid(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            u["plan"] = f"{days}_days"

            save_users(users)

            return extend_user(username, days)

    raise ValueError("USER_NOT_FOUND")