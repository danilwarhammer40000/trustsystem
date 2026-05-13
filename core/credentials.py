import os
import tempfile
from datetime import datetime
from filelock import FileLock

CREDENTIALS_PATH = "/opt/trusttunnel/credentials.toml"
LOCK_PATH = "/opt/trusttunnel/credentials.lock"

lock = FileLock(LOCK_PATH, timeout=10)


# =========================
# LOAD (SAFE PARSER)
# =========================

def load_credentials():
    """
    Парсит credentials.toml в безопасный список клиентов.
    Не падает при любом повреждении файла.
    """
    if not os.path.exists(CREDENTIALS_PATH):
        return {"client": []}

    clients = []

    try:
        with open(CREDENTIALS_PATH, "r") as f:
            current = {}

            for line in f:
                line = line.strip()

                # новый блок клиента
                if line == "[[client]]":
                    if current:
                        clients.append(current)
                    current = {}
                    continue

                # ключ = значение (универсально)
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"')
                    current[k] = v

            if current:
                clients.append(current)

        return {"client": clients}

    except Exception:
        return {"client": []}


# =========================
# ATOMIC WRITE
# =========================

def atomic_write(data: dict):
    """
    Полная перезапись credentials файла (source of truth = DB)
    """
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

    with lock:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=os.path.dirname(CREDENTIALS_PATH)
        ) as tmp:

            for client in data.get("client", []):
                username = client.get("username")
                password = client.get("password")

                if not username or not password:
                    continue

                tmp.write("[[client]]\n")
                tmp.write(f'username = "{username}"\n')
                tmp.write(f'password = "{password}"\n\n')

            tmp_path = tmp.name

        os.replace(tmp_path, CREDENTIALS_PATH)


# =========================
# REBUILD FROM DB (CORE LOGIC)
# =========================

def rebuild_credentials_from_db(users):
    """
    Полная синхронизация credentials с users.json.

    Правила:
    - только active пользователи
    - только не истёкшие подписки
    - дедуп по username
    - игнор битых данных
    """

    clients = []
    now = datetime.utcnow()

    seen = set()  # защита от дублей

    for u in users:
        # 1. только активные
        if u.get("status") != "active":
            continue

        # 2. проверка срока
        exp = u.get("expires_at")
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                if exp_dt < now:
                    continue
            except Exception:
                continue

        username = u.get("username")
        password = u.get("password")

        if not username or not password:
            continue

        # 3. дедуп
        if username in seen:
            continue

        seen.add(username)

        clients.append({
            "username": username,
            "password": password
        })

    atomic_write({"client": clients})


# =========================
# REMOVE USER
# =========================

def remove_user_from_credentials(username: str):
    """
    Удаляет конкретного пользователя из credentials.
    """
    data = load_credentials()

    data["client"] = [
        c for c in data.get("client", [])
        if c.get("username") != username
    ]

    atomic_write(data)