from core.db import load_users, save_users


def get_all():
    return load_users()


def get_by_username(username):
    for u in load_users():
        if u["username"] == username:
            return u
    return None


def get_by_tg(tg_id):
    for u in load_users():
        if str(u.get("telegram_id")) == str(tg_id):
            return u
    return None


def create(user):
    data = load_users()
    data.append(user)
    save_users(data)
    return user


def update(username, **fields):
    data = load_users()

    for u in data:
        if u["username"] == username:
            u.update(fields)
            break

    save_users(data)


def delete(username):
    data = [u for u in load_users() if u["username"] != username]
    save_users(data)