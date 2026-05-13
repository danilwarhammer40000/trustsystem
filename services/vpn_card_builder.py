from datetime import datetime
from services.user_service import get_user_by_tg
from core.generator import generate_link  # или откуда у тебя берётся ссылка
from config.settings import DOMAIN

def _format_date(dt_str):
    if not dt_str:
        return "∞"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str or "∞"

def build_vpn_card(tg_id: str):
    user = get_user_by_tg(tg_id)
    if not user:
        return {"text": "❌ Пользователь не найден"}

    username = user.get("username", f"user_{tg_id}")
    status = user.get("status", "inactive")
    expires_at = _format_date(user.get("expires_at"))
    
    # Если пользователь неактивен — всё равно показываем данные
    if status != "active":
        card_text = (
            f"👤 {username}\n"
            f"⚠️ Статус: {status.upper()}\n"
            f"⏳ Истекает: {expires_at}\n\n"
            f"🔴 Доступ неактивен"
        )
        return {"text": card_text}

    # Активный пользователь
    link = generate_link(username, DOMAIN) if 'generate_link' in globals() else f"https://example.com/connect/{username}"
    
    card_text = (
        f"👤 {username}\n"
        f"🔑 auto\n"
        f"⏳ {expires_at}\n\n"
        f"🔗 {link}\n\n"
        f"📱 Для подключения отсканируйте QR-код"
    )

    return {
        "text": card_text,
        "link": link,
        "username": username,
        "expires_at": expires_at
    }