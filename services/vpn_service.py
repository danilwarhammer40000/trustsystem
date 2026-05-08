from core.generator import generate_link
from config.settings import DOMAIN
from services.user_service import get_user


def get_vpn_link(username: str):
    user = get_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    if user.get("status") != "active":
        raise ValueError("USER_NOT_ACTIVE")

    link = generate_link(username, DOMAIN)

    return {
        "username": username,
        "password": user.get("password"),
        "link": link,
        "expires_at": user.get("expires_at")
    }