from services.vpn_service import get_vpn_link
from datetime import datetime


def _fmt(dt):
    if not dt:
        return "∞"
    try:
        return datetime.fromisoformat(dt).strftime("%Y-%m-%d")
    except:
        return dt


def get_vpn_card(username: str) -> str:
    vpn = get_vpn_link(username)

    link = vpn["link"]
    password = vpn["password"]
    expires = _fmt(vpn["expires_at"])

    payload = link.split("tt://?")[-1] if "tt://?" in link else ""

    return (
        f"👤 {username}\n"
        f"🔑 {password}\n"
        f"⏳ {expires}\n\n"
        f"🔗 {link}\n\n"
        f"https://trusttunnel.org/qr.html#tt={payload}"
    )