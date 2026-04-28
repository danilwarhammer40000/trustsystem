from datetime import datetime, timedelta

from core.db import load_users, save_users
from core.credentials import rebuild_credentials_from_db
from core.sync import full_sync


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
# CREATE
# =========================

def create_user(tg_id: int, username: str, password: str, plan: str = "trial"):
    users = load_users()

    # check duplicate tg
    for u in users:
        if str(u.get("telegram_id")) == str(tg_id):
            raise ValueError("USER_ALREADY_EXISTS")

    user = {
        "username": username,
        "password": password,
        "telegram_id": tg_id,
        "plan": plan,
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
# ACTIVATE TRIAL
# =========================

def activate_trial(username: str, days: int = 3):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            if u.get("trial_used"):
                raise ValueError("TRIAL_ALREADY_USED")

            expires = datetime.utcnow() + timedelta(days=days)

            u["status"] = "active"
            u["trial_used"] = True
            u["expires_at"] = expires.isoformat()

            save_users(users)
            full_sync()

            return u

    raise ValueError("USER_NOT_FOUND")


# =========================
# ACTIVATE PAID
# =========================

def activate_paid(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            base = datetime.utcnow()

            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"])
                    if old > base:
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
# EXTEND
# =========================

def extend_user(username: str, days: int):
    users = load_users()

    for u in users:
        if u.get("username") == username:

            base = datetime.utcnow()

            if u.get("expires_at"):
                try:
                    old = datetime.fromisoformat(u["expires_at"])
                    if old > base:
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
# DELETE / DEACTIVATE
# =========================

def delete_user(username: str):
    users = load_users()

    new_users = [u for u in users if u.get("username") != username]

    save_users(new_users)
    full_sync()


def deactivate_user(username: str):
    users = load_users()

    for u in users:
        if u.get("username") == username:
            u["status"] = "inactive"

    save_users(users)
    full_sync()
