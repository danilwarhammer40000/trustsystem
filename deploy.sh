#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM PRODUCTION DEPLOY ==="

PROJECT_DIR="/opt/trustsystem"
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

if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

# SAFE JSON VALIDATION (FIXED)
python3 - <<'EOF'
import json

path = "storage/users.json"

try:
    with open(path, "r") as f:
        json.load(f)
    print("users.json OK")

except Exception:
    print("CORRUPTED users.json → RESETTING")
    with open(path, "w") as f:
        f.write("[]")
EOF

# =========================
# 5. RESTART
# =========================
echo "[5] Restarting services..."

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service
systemctl restart trustsystem-webhook

# =========================
# 6. STATUS
# =========================
echo "[6] STATUS"

systemctl is-active trustsystem-admin.service
systemctl is-active trustsystem-public.service

echo "=== DEPLOY COMPLETE ==="