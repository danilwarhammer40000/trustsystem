#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM PRODUCTION DEPLOY ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="$PROJECT_DIR/systemd"
SYSTEMD_TARGET="/etc/systemd/system"

cd "$PROJECT_DIR"

# =========================
# 0. ENV BACKUP
# =========================
echo "[0] Backing up .env..."

ENV_BACKUP="/tmp/trustsystem.env.backup"

if [ -f ".env" ]; then
    cp ".env" "$ENV_BACKUP"
fi

# =========================
# 1. UPDATE CODE
# =========================
echo "[1] Updating repository..."

git fetch origin
git reset --hard origin/main

if [ -f "$ENV_BACKUP" ]; then
    cp "$ENV_BACKUP" ".env"
fi

# =========================
# 2. CLEAN
# =========================
echo "[2] Cleaning untracked files..."

git clean -fd \
  -e venv \
  -e storage \
  -e .env

# =========================
# 3. VENV
# =========================
echo "[3] Virtual environment setup..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install yookassa httpx --quiet || true

# =========================
# 4. STORAGE SAFETY
# =========================
echo "[4] Storage integrity check..."

mkdir -p storage

# backup перед проверкой
if [ -f storage/users.json ]; then
    cp storage/users.json /tmp/users.json.backup || true
fi

# если нет файла — создаём
if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

# безопасная проверка + восстановление
python3 - <<'EOF'
import json
import shutil
import os

path = "storage/users.json"
backup = "/tmp/users.json.backup"

try:
    with open(path, "r") as f:
        json.load(f)
    print("users.json OK")

except Exception:
    print("CORRUPTED users.json")

    if os.path.exists(backup):
        print("RESTORING FROM BACKUP")
        shutil.copy(backup, path)
    else:
        print("NO BACKUP → RESET")
        with open(path, "w") as f:
            f.write("[]")
EOF

# =========================
# 5. INSTALL SYSTEMD
# =========================
echo "[5] Installing systemd services..."

for file in "$SYSTEMD_DIR"/*; do
    name=$(basename "$file")

    if [ ! -f "$SYSTEMD_TARGET/$name" ]; then
        echo "Installing $name"
        cp "$file" "$SYSTEMD_TARGET/$name"
    else
        echo "Updating $name"
        cp "$file" "$SYSTEMD_TARGET/$name"
    fi
done

# перезагрузка systemd
systemctl daemon-reexec
systemctl daemon-reload

# =========================
# 6. ENABLE SERVICES & TIMERS
# =========================
echo "[6] Enabling services and timers..."

for file in "$SYSTEMD_DIR"/*; do
    name=$(basename "$file")

    if [[ "$name" == *.service ]]; then
        systemctl enable "$name" || true
    fi

    if [[ "$name" == *.timer ]]; then
        systemctl enable "$name" || true
        systemctl start "$name" || true
    fi
done

# =========================
# 7. RESTART SERVICES
# =========================
echo "[7] Restarting services..."

systemctl restart trustsystem-admin.service || true
systemctl restart trustsystem-public.service || true
systemctl restart trustsystem-webhook.service || true

# =========================
# 8. STATUS
# =========================
echo "[8] STATUS"

systemctl is-active trustsystem-admin.service || true
systemctl is-active trustsystem-public.service || true
systemctl is-active trustsystem-webhook.service || true

echo "=== DEPLOY COMPLETE ==="