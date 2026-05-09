from services.control_plane import sync_all_users


def safe_sync():
    """
    Wrapper для admin bot.
    Вся логика синхронизации находится в control_plane.
    """
    return sync_all_users()