# core/services/public_user_service.py

from services.user_service import (
    create_user,
    get_user,
    extend_user
)

from core.db import load_users, save_users
from datetime import datetime


def get_or_create_user_by_tg(tg_id: int, username: str | None = None):

    users = load_users()

    for u in users:
        if u.get("telegram_id") == tg_id:
            return u

    base_username = username or f"user{tg_id}"

    # защита от дублей
    existing = {u["username"] for u in users}

    final = base_username
    i = 1

    while final in existing:
        final = f"{base_username}{i}"
        i += 1

    return create_user(final, tg_id=tg_id)


def activate_trial_by_tg(tg_id: int):
    user = get_or_create_user_by_tg(tg_id)

    if user.get("trial_used"):
        raise ValueError("TRIAL_ALREADY_USED")

    user["trial_used"] = True
    user["plan"] = "trial"

    save_users(load_users())

    return extend_user(user["username"], 3)


def get_user_by_tg(tg_id: int):
    users = load_users()

    for u in users:
        if u.get("telegram_id") == tg_id:
            return u

    return None