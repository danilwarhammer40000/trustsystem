from services.user_service import create_user, get_user_by_tg

def get_or_create(tg_id):
    user = get_user_by_tg(tg_id)
    if user:
        return user
    return create_user(tg_id)

def get_by_tg(tg_id):
    return get_user_by_tg(tg_id)