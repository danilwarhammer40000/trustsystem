from datetime import datetime, timedelta
import secrets
import string
import re

from core.db import load_users, save_users


# =========================
# INTERNAL HELPERS
# =========================

def _generate_password(length: int = 12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _validate_username(username: str):
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        raise ValueError("INVALID_USERNAME")


def _save(users):
    save_users(users)


# =========================
# READ
# =========================

def get_all_users():
    return load_users()


def get_user(username: str):
    users = load_users()
    for u in users:
        if u.get("username") == username:
            return u
    return None


# =========================
# CREATE
# =========================

def create_user(username: str, password: str | None = None, tg_id: int | None = None):
    _validate_username(username)

    users = load_users()

    # Проверка на существование username
    for u in users:
        if u.get("username") == username:
            raise ValueError("USERNAME_TAKEN")

    # Если пользователь с таким telegram_id уже есть — возвращаем его
    if tg_id is not None:
        for u in users:
            if u.get("telegram_id") == tg_id:
                return u

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
    _save(users)

    return user


# =========================
# CORE TIME LOGIC
# =========================

def extend_user(username: str, days: int):
    """
    Улучшенная функция продления — надёжно работает с триалом и повторными оплатами.
    """
    users = load_users()

    for u in users:
        if u.get("username") == username:
            now = datetime.utcnow()

            if days == 0:
                u["status"] = "active"
                u["expires_at"] = "2099-12-31T23:59:59"
                _save(users)
                return u

            # === УЛУЧШЕННАЯ ЛОГИКА ===
            if u.get("expires_at"):
                try:
                    # Поддержка разных форматов ISO (с Z и без)
                    expires_str = u["expires_at"].replace("Z", "+00:00")
                    old_expires = datetime.fromisoformat(expires_str)

                    # Если срок уже истёк — начинаем от текущего времени
                    if old_expires < now:
                        base = now
                    else:
                        base = old_expires
                except Exception:
                    base = now
            else:
                base = now

            new_expiry = base + timedelta(days=days)

            u["status"] = "active"
            u["expires_at"] = new_expiry.isoformat()

            _save(users)
            return u

    raise ValueError("USER_NOT_FOUND")


def set_expire(username: str, dt: datetime):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["expires_at"] = dt.isoformat()
            u["status"] = "active" if dt > datetime.utcnow() else "inactive"
            _save(users)
            return u

    raise ValueError("USER_NOT_FOUND")


def delete_user(username: str):
    users = load_users()
    users = [u for u in users if u.get("username") != username]
    _save(users)


# =========================
# TRIAL
# =========================

def activate_trial(username: str):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            if u.get("trial_used"):
                raise ValueError("TRIAL_ALREADY_USED")

            u["trial_used"] = True
            u["plan"] = "trial"
            u["status"] = "active"
            u["expires_at"] = (datetime.utcnow() + timedelta(days=3)).isoformat()

            _save(users)
            return u

    raise ValueError("USER_NOT_FOUND")


# =========================
# PAID PLAN
# =========================

def activate_paid(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["plan"] = f"{days}_days"
            # Вызываем улучшенную функцию продления
            return extend_user(username, days)

    raise ValueError("USER_NOT_FOUND")