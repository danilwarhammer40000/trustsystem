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
# ACTIVATE ACCESS (ENTRYPOINT)
# =========================

def activate_access(username: str, plan: str = "trial"):
    from services.user_service import activate_trial, activate_paid

    if plan == "trial":
        user = activate_trial(username)
    else:
        user = activate_paid(username, 30)

    return user


# =========================
# EXTEND ACCESS
# =========================

def extend_access(username: str, days: int):
    from services.user_service import extend_user

    user = extend_user(username, days)

    return user


# =========================
# MANUAL SYNC (ADMIN ONLY)
# =========================

def rebuild_access():
    from core.sync import full_sync

    full_sync()
    return "OK"