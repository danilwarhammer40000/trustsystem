#!/bin/bash

echo "=== DEPLOY START ==="

cd /opt/trustsystem || exit

echo "[1] Pulling updates..."
git pull origin main

echo "[2] Activating venv..."
source venv/bin/activate

echo "[3] Installing dependencies..."
pip install -r requirements.txt

echo "[4] Restarting services..."
systemctl restart trustsystem-admin
systemctl restart trustsystem-public

echo "[5] Status:"
systemctl is-active trustsystem-admin
systemctl is-active trustsystem-public

echo "=== DEPLOY DONE ==="