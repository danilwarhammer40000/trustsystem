from datetime import datetime, timedelta
import secrets
import string

from core.repository import users_repo
from core.sync import full_sync


# ---------------- UTILS ----------------

def _generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def _calc_expiry(days: int):
    if days == 0:
        return None
    return (datetime.utcnow() + timedelta(days=days)).isoformat()


# ---------------- CREATE ----------------

def create_user(tg_id: int, username: str, days: int):
    if users_repo.get_by_tg(tg_id):
        raise Exception("USER_ALREADY_EXISTS")

    if users_repo.get_by_username(username):
        raise Exception("USERNAME_TAKEN")

    user = {
        "username": username,
        "password": _generate_password(),
        "telegram_id": tg_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": _calc_expiry(days),
        "status": "active"
    }

    users_repo.create(user)

    # атомарный sync
    full_sync()

    return user


# ---------------- EXTEND ----------------

def extend_user(username: str, days: int):
    user = users_repo.get_by_username(username)

    if not user:
        raise Exception("USER_NOT_FOUND")

    now = datetime.utcnow()

    if user.get("expires_at"):
        current = datetime.fromisoformat(user["expires_at"])
        base = current if current > now else now
    else:
        base = now

    new_exp = None if days == 0 else (base + timedelta(days=days)).isoformat()

    users_repo.update(
        username,
        expires_at=new_exp,
        status="active"
    )

    full_sync()

    return users_repo.get_by_username(username)


# ---------------- DELETE ----------------

def delete_user(username: str):
    if not users_repo.get_by_username(username):
        raise Exception("USER_NOT_FOUND")

    users_repo.delete(username)

    full_sync()


# ---------------- GET ----------------

def get_user(username: str):
    return users_repo.get_by_username(username)


def list_users():
    return users_repo.get_all()