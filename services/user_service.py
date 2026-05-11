from datetime import datetime, timedelta
import secrets
import string
import re

from core.db import load_users, save_users


def _generate_password(length: int = 12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in alphabet[:length])


def _validate_username(username: str):
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        raise ValueError("INVALID_USERNAME")


def get_all_users():
    return load_users()


def get_user(username: str):
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


def create_user(username: str, password: str | None = None, tg_id: int | None = None):
    _validate_username(username)

    users = load_users()

    if any(u.get("username") == username for u in users):
        raise ValueError("USERNAME_TAKEN")

    password = password if password and password != "-" else _generate_password()

    user = {
        "username": username,
        "password": password,
        "telegram_id": tg_id,
        "plan": "trial" if tg_id else "manual",
        "status": "inactive",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None
    }

    users.append(user)
    save_users(users)

    return user


# =========================
# CORE FIXED EXTENSION LOGIC
# =========================

def extend_user(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            now = datetime.utcnow()

            if days == 0:
                u["status"] = "active"
                u["expires_at"] = "2099-12-31T23:59:59"
                save_users(users)
                return u

            base = now

            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"])
                    if old > now:
                        base = old
                except:
                    pass

            u["expires_at"] = (base + timedelta(days=days)).isoformat()
            u["status"] = "active"

            save_users(users)
            return u

    raise ValueError("USER_NOT_FOUND")


def activate_paid(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            u["plan"] = f"{days}_days"

            # SINGLE SOURCE OF TRUTH
            return extend_user(username, days)

    raise ValueError("USER_NOT_FOUND")