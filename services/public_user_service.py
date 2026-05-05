from services.user_service import create_user
from core.db import load_users

def _gen_username(tg_id: int):
    return f"user_{tg_id}"

def get_or_create(tg_id: int):
    users = load_users()

    for u in users:
        if u.get("telegram_id") == tg_id:
            return u

    username = _gen_username(tg_id)

    return create_user(
        username=username,
        tg_id=tg_id
    )

def get_by_tg(tg_id: int):
    users = load_users()

    for u in users:
        if u.get("telegram_id") == tg_id:
            return u

    return None