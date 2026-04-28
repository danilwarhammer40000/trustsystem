from datetime import datetime, timedelta
import secrets
import string

from core.repository import users_repo
from core.credentials import rebuild_credentials_from_db
from core.sync import restart_trusttunnel


def _generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def create_user(tg_id: int, username: str, days: int):
    if users_repo.get_by_tg(tg_id):
        raise Exception("USER_ALREADY_EXISTS")

    if users_repo.get_by_username(username):
        raise Exception("USERNAME_TAKEN")

    password = _generate_password()

    expires = None
    if days > 0:
        expires = (datetime.utcnow() + timedelta(days=days)).isoformat()

    user = {
        "username": username,
        "password": password,
        "telegram_id": tg_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires,
        "status": "active" if days != 0 else "active"
    }

    users_repo.create(user)

    # 🔥 ВАЖНО — атомарный sync
    users = users_repo.get_all()
    rebuild_credentials_from_db(users)
    restart_trusttunnel()

    return user