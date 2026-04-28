from core.generator import generate_link
from core.sync import full_sync
from core.db import get_user


# =========================
# VPN LINK GENERATION
# =========================

def get_vpn_link(username: str, domain: str):
    user = get_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    link = generate_link(username, domain)

    return {
        "username": username,
        "password": user.get("password"),
        "link": link,
        "expires_at": user.get("expires_at"),
        "status": user.get("status")
    }


# =========================
# REBUILD ACCESS (SYNC SAFE)
# =========================

def rebuild_access():
    full_sync()
    return "OK"


# =========================
# EXTEND ACCESS FLOW WRAPPER
# =========================

def extend_access(username: str, days: int):
    from services.user_service import extend_user

    user = extend_user(username, days)
    full_sync()

    return {
        "username": user["username"],
        "expires_at": user["expires_at"],
        "status": user["status"]
    }


# =========================
# CREATE ACCESS WRAPPER
# =========================

def activate_access(username: str, plan: str = "trial"):
    from services.user_service import activate_trial, activate_paid

    if plan == "trial":
        user = activate_trial(username)
    else:
        user = activate_paid(username, 30)

    full_sync()

    return {
        "username": user["username"],
        "expires_at": user["expires_at"],
        "status": user["status"]
    }
