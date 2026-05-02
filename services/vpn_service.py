from core.generator import generate_link
from config.settings import DOMAIN

from services.user_service import get_user


# =========================
# VPN LINK
# =========================

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


# =========================
# ACTIVATE ACCESS
# =========================

def activate_access(username: str, plan: str):
    from services.user_service import activate_trial, activate_paid

    if plan == "trial":
        return activate_trial(username)

    if plan == "30":
        return activate_paid(username, 30)

    if plan == "60":
        return activate_paid(username, 60)

    raise ValueError("INVALID_PLAN")


# =========================
# EXTEND ACCESS
# =========================

def extend_access(username: str, days: int):
    from services.user_service import extend_user
    return extend_user(username, days)


# =========================
# SYNC
# =========================

def rebuild_access():
    from core.sync import full_sync
    full_sync()
    return "OK"