from datetime import datetime

from services.vpn_service import get_vpn_link


def _format_date(dt_str: str | None) -> str:
    if not dt_str:
        return "∞"

    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d")
    except:
        return dt_str


def build_vpn_card(username: str) -> dict:
    """
    Возвращает структурированную VPN-карточку
    для Telegram/бота/webhook.
    """

    vpn = get_vpn_link(username)

    link = vpn.get("link", "")
    password = vpn.get("password", "")
    expires_at = _format_date(vpn.get("expires_at"))

    # извлекаем payload для QR
    qr_payload = ""
    if "tt://?" in link:
        qr_payload = link.split("tt://?")[-1]

    card_text = (
        f"👤 {username}\n"
        f"🔑 {password}\n"
        f"⏳ {expires_at}\n\n"
        f"🔗 {link}\n\n"
        f"To connect on mobile, scan QR:\n"
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