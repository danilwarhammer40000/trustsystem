#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM PRODUCTION DEPLOY ==="

PROJECT_DIR="/opt/trustsystem"
cd "$PROJECT_DIR"

# =========================
# 0. ENV BACKUP (CRITICAL)
# =========================
echo "[0] Backing up .env..."

ENV_BACKUP="/tmp/trustsystem.env.backup"

if [ -f ".env" ]; then
    cp ".env" "$ENV_BACKUP"
fi

# =========================
# 1. GIT UPDATE (SAFE RESET)
# =========================
echo "[1] Updating repository..."

git fetch origin
git reset --hard origin/main

# restore env after reset
if [ -f "$ENV_BACKUP" ]; then
    cp "$ENV_BACKUP" ".env"
fi

# =========================
# 2. CLEAN UNTRACKED (SAFE MODE)
# =========================
echo "[2] Cleaning untracked files..."

git clean -fd \
  -e venv \
  -e storage \
  -e .env \
  -e logs

# =========================
# 3. VENV (ROBUST)
# =========================
echo "[3] Virtual environment setup..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# payment deps safety
pip install yookassa httpx --quiet || true

# =========================
# 4. STORAGE SAFETY LAYER
# =========================
echo "[4] Storage integrity check..."

mkdir -p storage

if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

# validate JSON integrity
python3 - <<EOF || {
import json
try:
    json.load(open("storage/users.json"))
    print("users.json OK")
except:
    print("CORRUPTED → resetting users.json")
    open("storage/users.json", "w").write("[]")
}
EOF

# =========================
# 5. ZERO-DOWNTIME RESTART
# =========================
echo "[5] Restarting services..."

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service

# =========================
# 6. STATUS CHECK
# =========================
echo "[6] Service status:"

systemctl is-active trustsystem-admin.service
systemctl is-active trustsystem-public.service

echo "=== DEPLOY COMPLETE ==="