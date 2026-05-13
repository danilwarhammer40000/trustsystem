from datetime import datetime
from services.vpn_service import get_vpn_link


def _format_date(dt_str: str | None) -> str:
    if not dt_str:
        return "∞"

    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return dt_str or "∞"


def build_vpn_card(telegram_id: str) -> dict:
    """
    Вся логика теперь строится от TG-ID
    """

    vpn = get_vpn_link(telegram_id)

    link = vpn.get("link", "")
    password = vpn.get("password", "")
    username = vpn.get("username", "")
    expires_at = _format_date(vpn.get("expires_at"))

    qr_payload = f"user={username}"

    # fallback логика (если появится иной формат link)
    if "connect/" in link:
        try:
            qr_payload = link.rstrip("/").split("/")[-1]
        except Exception:
            qr_payload = username

    card_text = (
        f"👤 {username}\n"
        f"🔑 {password}\n"
        f"⏳ {expires_at}\n\n"
        f"🔗 {link}\n\n"
        f"Scan QR:\n"
        f"https://trusttunnel.org/qr.html#tt={qr_payload}"
    )

    return {
        "text": card_text,
        "link": link,
        "qr_payload": qr_payload,
        "username": username,
        "password": password,
        "expires_at": expires_at
    }