#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM SAFE PRODUCTION DEPLOY v3.2 (Simple Pull) ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="/etc/systemd/system"

cd "$PROJECT_DIR"

# =========================
# 0. BACKUP (критически важные файлы)
# =========================
echo "[0] Creating backup of runtime files..."

BACKUP_DIR="/tmp/trustsystem_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -n .env "$BACKUP_DIR/.env" 2>/dev/null || true
cp -n storage/users.json "$BACKUP_DIR/users.json" 2>/dev/null || true
cp -n storage/payments.json "$BACKUP_DIR/payments.json" 2>/dev/null || true

echo "   Backup created: $BACKUP_DIR"

# =========================
# 1. GIT UPDATE (ПРОСТОЙ GIT PULL)
# =========================
echo "[1] Updating code with git pull..."

git fetch origin --prune

if git pull origin main; then
    echo "   ✅ Git pull completed successfully"
else
    echo "   ❌ Git pull failed! Please check repository status manually."
    exit 1
fi

# =========================
# 2. ENSURE RUNTIME FILES (защита .env и json)
# =========================
echo "[2] Ensuring runtime files exist..."

mkdir -p storage

if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file is missing! Create it manually."
fi

if [ ! -f "storage/users.json" ]; then
    echo "[]" > storage/users.json
    echo "   Created empty users.json"
fi

if [ ! -f "storage/payments.json" ]; then
    echo "[]" > storage/payments.json
    echo "   Created empty payments.json"
fi

# =========================
# 3. VIRTUAL ENVIRONMENT
# =========================
echo "[3] Setting up Python environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Created new virtual environment"
fi

source venv/bin/activate

pip install --upgrade pip setuptools wheel --quiet
pip install -r requirements.txt --quiet
pip install yookassa fastapi uvicorn aiogram redis filelock httpx --quiet

deactivate

echo "   Dependencies updated"

# =========================
# 4. SYSTEMD SERVICES
# =========================
echo "[4] Updating systemd services..."

for service_file in systemd/*.service; do
    if [ -f "$service_file" ]; then
        service_name=$(basename "$service_file")
        cp "$service_file" "$SYSTEMD_DIR/$service_name"
        echo "   Updated $service_name"
    fi
done

systemctl daemon-reload

# =========================
# 5. RESTART SERVICES
# =========================
echo "[5] Restarting services..."

services=(
    trustsystem-webhook.service
    trustsystem-public.service
    trustsystem-admin.service
)

for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        echo "   Restarting $service"
        systemctl restart "$service" || echo "   Warning: Failed to restart $service"
    fi
done

# Таймеры
systemctl restart trustsystem-sync.timer 2>/dev/null || true
systemctl restart trustsystem-expire.timer 2>/dev/null || true

# =========================
# 6. FINAL STATUS
# =========================
echo "[6] Final status:"

for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        echo "   $service → $status"
    fi
done

echo ""
echo "=== DEPLOY COMPLETE SUCCESSFULLY ==="
echo "Время: $(date)"