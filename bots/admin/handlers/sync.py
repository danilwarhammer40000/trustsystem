from services.control_plane import sync_all_users


async def safe_sync():
    """
    Вызов из admin bot
    """
    try:
        return sync_all_users()
    except Exception as e:
        return f"❌ Sync error: {e}"