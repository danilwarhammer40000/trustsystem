from core.generator import generate_link
from config.settings import DOMAIN
from services.user_service import get_user_by_tg


def get_vpn_link(telegram_id: str):
    """
    TG-ID = источник истины
    username больше не используется как primary key
    """

    user = get_user_by_tg(int(telegram_id))

    if not user:
        raise ValueError("USER_NOT_FOUND")

    if user.get("status") != "active":
        raise ValueError("USER_NOT_ACTIVE")

    username = user.get("username")

    if not username:
        raise ValueError("USERNAME_MISSING")

    link = generate_link(username, DOMAIN)

    return {
        "telegram_id": str(telegram_id),
        "username": username,
        "password": user.get("password"),
        "link": link,
        "expires_at": user.get("expires_at")
    }