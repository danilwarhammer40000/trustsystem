#!/bin/bash

set -e

echo "=== DEPLOY START ==="

PROJECT_DIR="/opt/trustsystem"

cd $PROJECT_DIR

# =========================
# 1. FETCH LATEST CODE
# =========================
echo "[1] Fetching updates..."
git fetch origin

echo "[2] Hard reset to origin/main..."
git reset --hard origin/main

# =========================
# 3. REMOVE UNTRACKED FILES (SAFE)
# =========================
echo "[3] Cleaning untracked files..."
git clean -fd -e venv -e storage

# =========================
# 4. VENV SETUP (REBUILD SAFE)
# =========================
echo "[4] Setting up venv..."

if [ ! -d "venv" ]; then
    echo "[*] Creating venv..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# =========================
# 5. SAFE STORAGE CHECK
# =========================
echo "[5] Checking storage..."

mkdir -p storage

if [ ! -f storage/users.json ]; then
    echo "[]" > storage/users.json
fi

# =========================
# 6. RESTART SERVICES
# =========================
echo "[6] Restarting services..."

systemctl restart trustsystem-admin
systemctl restart trustsystem-public

# =========================
# 7. STATUS
# =========================
echo "=== DEPLOY COMPLETE ==="

systemctl status trustsystem-admin --no-pager | head -n 10
systemctl status trustsystem-public --no-pager | head -n 10