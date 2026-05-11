#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM SAFE PRODUCTION DEPLOY ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="/etc/systemd/system"
cd "$PROJECT_DIR"

# =========================
# 0. BACKUP (только если есть)
# =========================
echo "[0] Backup env + storage..."

ENV_BACKUP="/tmp/trustsystem.env.backup"
USERS_BACKUP="/tmp/users.json.backup"

[ -f ".env" ] && cp -n ".env" "$ENV_BACKUP" || true
[ -f "storage/users.json" ] && cp -n "storage/users.json" "$USERS_BACKUP" || true

# =========================
# 1. GIT UPDATE (БЕЗ УДАЛЕНИЯ ФАЙЛОВ)
# =========================
echo "[1] Git update (safe reset)..."

git fetch origin
git reset --hard origin/main

# ВАЖНО: возвращаем ENV назад
[ -f "$ENV_BACKUP" ] && cp "$ENV_BACKUP" ".env"

# =========================
# 2. НЕ ДЕЛАЕМ git clean fd
# =========================
echo "[2] Skip git clean (to protect env/storage)"

# =========================
# 3. VENV
# =========================
echo "[3] Python env..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install yookassa httpx --quiet || true

# =========================
# 4. STORAGE SAFE CHECK
# =========================
echo "[4] Storage safety check..."

mkdir -p storage

[ -f storage/users.json ] || echo "[]" > storage/users.json

python3 - <<'EOF'
import json, shutil, os

path = "storage/users.json"
backup = "storage/users.backup.json"

if os.path.exists(path):
    shutil.copy(path, backup)

try:
    json.load(open(path))
    print("users.json OK")
except:
    print("CORRUPTED → restore")
    if os.path.exists(backup):
        shutil.copy(backup, path)
    else:
        open(path, "w").write("[]")
EOF

# =========================
# 5. SYSTEMD FIX (ВАЖНО ДЛЯ ENV)
# =========================
echo "[5] Fix systemd env injection..."

for file in systemd/*.service; do
    name=$(basename "$file")

    # добавляем .env если его нет
    if ! grep -q "EnvironmentFile" "$file"; then
        echo "Adding EnvironmentFile to $name"

        sed -i '/^\[Service\]/a EnvironmentFile=/opt/trustsystem/.env' "$file"
    fi

    cp "$file" "$SYSTEMD_DIR/$name"
done

systemctl daemon-reexec
systemctl daemon-reload

# =========================
# 6. RESTART
# =========================
echo "[6] Restart services..."

systemctl restart trustsystem-webhook.service || true
systemctl restart trustsystem-public.service || true
systemctl restart trustsystem-admin.service || true

systemctl restart trustsystem-sync.timer || true
systemctl restart trustsystem-expire.timer || true

# =========================
# 7. STATUS
# =========================
echo "[7] Status"

systemctl is-active trustsystem-webhook.service || true
systemctl is-active trustsystem-public.service || true
systemctl is-active trustsystem-admin.service || true

echo "=== DEPLOY SAFE COMPLETE ==="