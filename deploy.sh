#!/bin/bash
set -e

echo "=== DEPLOY START ==="

PROJECT_DIR="/opt/trustsystem"

cd "$PROJECT_DIR" || exit 1

echo "[1] Fetching updates..."
git fetch origin

echo "[2] Resetting local changes..."
git reset --hard origin/main

echo "[3] Cleaning untracked files..."
git clean -fd

echo "[4] Activating venv..."
source venv/bin/activate

echo "[5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# если используешь YooKassa
pip install yookassa httpx || true

echo "[6] Restarting services..."
systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service

echo "[7] Status:"
systemctl is-active trustsystem-admin.service
systemctl is-active trustsystem-public.service

echo "=== DEPLOY DONE ==="