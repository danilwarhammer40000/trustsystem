from datetime import datetime, timedelta
import secrets
import string
import re

from core.db import load_users, save_users


# =========================
# HELPERS
# =========================

def _generate_password(length: int = 12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _save(users):
    save_users(users)


def _gen_username(tg_id: int):
    return f"user_{tg_id}"


# =========================
# CORE
# =========================

def get_user_by_tg(tg_id: str | int):
    users = load_users()

    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):
            return u

    return None


def create_user_if_not_exists(tg_id: str | int):
    users = load_users()

    # уже есть
    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):
            return u

    username = _gen_username(tg_id)

    user = {
        "username": username,
        "password": _generate_password(),
        "telegram_id": int(tg_id),
        "plan": "trial",
        "status": "inactive",
        "trial_used": False,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None
    }

    users.append(user)
    _save(users)

    return user


# =========================
# TIME LOGIC
# =========================

def extend_user_by_tg(tg_id: str | int, days: int):
    users = load_users()

    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):
            now = datetime.utcnow()

            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"].replace("Z", "+00:00"))
                    base = old if old > now else now
                except:
                    base = now
            else:
                base = now

            new_expiry = base + timedelta(days=days)

            u["status"] = "active"
            u["expires_at"] = new_expiry.isoformat()
            u["plan"] = f"{days}_days"

            _save(users)
            return u

    raise ValueError("USER_NOT_FOUND")


# =========================
# TRIAL
# =========================

def activate_trial_by_tg(tg_id: str | int):
    users = load_users()

    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):

            if u.get("trial_used"):
                raise ValueError("TRIAL_ALREADY_USED")

            u["trial_used"] = True
            u["plan"] = "trial"
            u["status"] = "active"
            u["expires_at"] = (datetime.utcnow() + timedelta(days=3)).isoformat()

            _save(users)
            return u

    raise ValueError("USER_NOT_FOUND")