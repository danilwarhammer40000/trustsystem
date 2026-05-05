#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM PRODUCTION DEPLOY ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="/etc/systemd/system"
cd "$PROJECT_DIR"

# =========================
# 0. BACKUPS
# =========================
echo "[0] Backups..."

ENV_BACKUP="/tmp/trustsystem.env.backup"
USERS_BACKUP="/tmp/users.json.backup"

[ -f ".env" ] && cp ".env" "$ENV_BACKUP"
[ -f "storage/users.json" ] && cp "storage/users.json" "$USERS_BACKUP"

# =========================
# 1. GIT UPDATE + LOG
# =========================
echo "[1] Updating repository..."

git fetch origin

echo "----- INCOMING CHANGES -----"
git log HEAD..origin/main --oneline || true

echo "----- FILE CHANGES -----"
git diff --name-status HEAD origin/main || true

git reset --hard origin/main

[ -f "$ENV_BACKUP" ] && cp "$ENV_BACKUP" ".env"

# =========================
# 2. CLEAN
# =========================
echo "[2] Cleaning..."

git clean -fd \
  -e venv \
  -e storage \
  -e .env

# =========================
# 3. VENV
# =========================
echo "[3] Python environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install yookassa httpx --quiet || true

# =========================
# 4. STORAGE SAFE
# =========================
echo "[4] Storage check..."

mkdir -p storage

if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

python3 - <<'EOF'
import json, shutil, os

path = "storage/users.json"
backup = "storage/users.backup.json"

if os.path.exists(path):
    shutil.copy(path, backup)

try:
    with open(path) as f:
        json.load(f)
    print("users.json OK")

except Exception:
    print("CORRUPTED users.json → RESTORING")

    if os.path.exists(backup):
        shutil.copy(backup, path)
    else:
        print("NO BACKUP → EMPTY FILE")
        with open(path, "w") as f:
            f.write("[]")
EOF

# =========================
# 5. INSTALL SYSTEMD
# =========================
echo "[5] Installing systemd services..."

for file in systemd/*; do
    name=$(basename "$file")

    if [ ! -f "$SYSTEMD_DIR/$name" ]; then
        echo "Installing $name"
        cp "$file" "$SYSTEMD_DIR/$name"
    else
        echo "Updating $name"
        cp "$file" "$SYSTEMD_DIR/$name"
    fi
done

systemctl daemon-reexec
systemctl daemon-reload

# enable timers/services
for file in systemd/*; do
    name=$(basename "$file")

    if [[ "$name" == *.service ]] || [[ "$name" == *.timer ]]; then
        systemctl enable "$name" || true
    fi
done

# =========================
# 6. RESTART
# =========================
echo "[6] Restarting services..."

systemctl restart trustsystem-admin.service || true
systemctl restart trustsystem-public.service || true
systemctl restart trustsystem-webhook.service || true

# timers
systemctl restart trustsystem-expire.timer || true
systemctl restart trustsystem-sync.timer || true

# =========================
# 7. STATUS
# =========================
echo "[7] STATUS"

systemctl is-active trustsystem-admin.service
systemctl is-active trustsystem-public.service
systemctl is-active trustsystem-webhook.service

echo "----- TIMERS -----"
systemctl list-timers --all | grep trustsystem || true

echo "=== DEPLOY COMPLETE ==="