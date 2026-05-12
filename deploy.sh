#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM SAFE PRODUCTION DEPLOY v3.3 (Worker Enabled) ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="/etc/systemd/system"

cd "$PROJECT_DIR"

# =========================
# 0. BACKUP
# =========================
echo "[0] Creating backup of runtime files..."

BACKUP_DIR="/tmp/trustsystem_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -n .env "$BACKUP_DIR/.env" 2>/dev/null || true
cp -n storage/users.json "$BACKUP_DIR/users.json" 2>/dev/null || true
cp -n storage/payments.json "$BACKUP_DIR/payments.json" 2>/dev/null || true
cp -n storage/queue.json "$BACKUP_DIR/queue.json" 2>/dev/null || true

echo "   Backup created: $BACKUP_DIR"

# =========================
# 1. GIT UPDATE
# =========================
echo "[1] Updating code with git pull..."

git fetch origin --prune

if git pull origin main; then
    echo "   ✅ Git pull completed successfully"
else
    echo "   ❌ Git pull failed!"
    exit 1
fi

# =========================
# 2. ENSURE FILES
# =========================
echo "[2] Ensuring runtime files exist..."

mkdir -p storage

[ -f ".env" ] || echo "⚠️  WARNING: .env missing"

[ -f "storage/users.json" ] || echo "[]" > storage/users.json
[ -f "storage/payments.json" ] || echo "[]" > storage/payments.json
[ -f "storage/queue.json" ] || echo "[]" > storage/queue.json   # 🔥 НОВОЕ

# =========================
# 3. VENV
# =========================
echo "[3] Setting up Python environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet
pip install yookassa fastapi uvicorn aiogram redis filelock httpx --quiet

deactivate

echo "   Dependencies updated"

# =========================
# 4. SYSTEMD
# =========================
echo "[4] Updating systemd services..."

for service_file in systemd/*.service; do
    cp "$service_file" "$SYSTEMD_DIR/$(basename "$service_file")"
done

systemctl daemon-reload

# =========================
# 5. RESTART
# =========================
echo "[5] Restarting services..."

services=(
    trustsystem-webhook.service
    trustsystem-public.service
    trustsystem-admin.service
    trustsystem-worker.service   # 🔥 НОВОЕ
)

for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        echo "   Restarting $service"
        systemctl restart "$service" || echo "   Warning: Failed $service"
    fi
done

systemctl restart trustsystem-sync.timer 2>/dev/null || true
systemctl restart trustsystem-expire.timer 2>/dev/null || true

# =========================
# 6. STATUS
# =========================
echo "[6] Final status:"

for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        echo "   $service → $(systemctl is-active $service)"
    fi
done

echo ""
echo "=== DEPLOY COMPLETE ==="
echo "Time: $(date)"