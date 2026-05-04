#!/bin/bash

set -e

echo "=== DEPLOY START ==="

PROJECT_DIR="/opt/trustsystem"

cd "$PROJECT_DIR"

# =========================
# 0. PROTECT .ENV (HARD SAFETY)
# =========================
echo "[0] Protecting .env..."

if [ -f .env ]; then
    cp .env /tmp/trustsystem.env.backup
fi

# =========================
# 1. FETCH LATEST CODE
# =========================
echo "[1] Fetching updates..."
git fetch origin

echo "[2] Hard reset to origin/main..."
git reset --hard origin/main

# restore env after reset (SAFETY NET)
if [ -f /tmp/trustsystem.env.backup ]; then
    cp /tmp/trustsystem.env.backup .env
fi

# =========================
# 2. CLEAN UNTRACKED FILES (SAFE MODE)
# =========================
echo "[3] Cleaning untracked files..."

git clean -fd \
  -e venv \
  -e storage \
  -e .env

# =========================
# 3. VENV SETUP (SAFE)
# =========================
echo "[4] Setting up venv..."

if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "[*] Recreating venv..."
    rm -rf venv
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# =========================
# 4. STORAGE CHECK
# =========================
echo "[5] Checking storage..."

mkdir -p storage

if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

# =========================
# 5. RESTART SERVICES
# =========================
echo "[6] Restarting services..."

systemctl restart trustsystem-admin
systemctl restart trustsystem-public

# =========================
# 6. STATUS
# =========================
echo "=== DEPLOY COMPLETE ==="

systemctl status trustsystem-admin --no-pager | head -n 10
systemctl status trustsystem-public --no-pager | head -n 10