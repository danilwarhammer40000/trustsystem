#!/bin/bash
set -euo pipefail

echo "=== TRUSTSYSTEM SAFE PRODUCTION DEPLOY v2 ==="

PROJECT_DIR="/opt/trustsystem"
SYSTEMD_DIR="/etc/systemd/system"
cd "$PROJECT_DIR"

# =========================
# 0. BACKUP (ТОЛЬКО НА ВСЯКИЙ СЛУЧАЙ)
# =========================
echo "[0] Backup runtime state..."

mkdir -p /tmp/trustsystem_backup

[ -f ".env" ] && cp -n ".env" /tmp/trustsystem_backup/.env || true
[ -f "storage/users.json" ] && cp -n "storage/users.json" /tmp/trustsystem_backup/users.json || true

# =========================
# 1. GIT UPDATE (SAFE)
# =========================
echo "[1] Updating code..."

git fetch origin
git reset --hard origin/main

# ❗ ВАЖНО: НИЧЕГО НЕ ВОССТАНАВЛИВАЕМ В .env И STORAGE

# =========================
# 2. ENSURE RUNTIME FILES EXIST (NO OVERWRITE)
# =========================
echo "[2] Ensure runtime files..."

mkdir -p storage

if [ ! -f ".env" ]; then
    echo "[WARN] .env missing (must be created manually once)"
fi

if [ ! -f "storage/users.json" ]; then
    echo "[]" > storage/users.json
fi

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
pip install yookassa httpx redis fastapi uvicorn aiogram

deactivate

# =========================
# 4. SYSTEMD (ONLY CODE UPDATE)
# =========================
echo "[4] Systemd update..."

for file in systemd/*.service; do
    name=$(basename "$file")

    # НЕ дублируем EnvironmentFile каждый раз
    if ! grep -q "EnvironmentFile" "$file"; then
        sed -i '/^\[Service\]/a EnvironmentFile=/opt/trustsystem/.env' "$file"
    fi

    cp "$file" "$SYSTEMD_DIR/$name"
done

systemctl daemon-reload

# =========================
# 5. RESTART SERVICES (SAFE)
# =========================
echo "[5] Restart services..."

systemctl restart trustsystem-webhook.service || true
systemctl restart trustsystem-public.service || true
systemctl restart trustsystem-admin.service || true

systemctl restart trustsystem-sync.timer || true
systemctl restart trustsystem-expire.timer || true

# =========================
# 6. STATUS
# =========================
echo "[6] Status check..."

systemctl is-active trustsystem-webhook.service || true
systemctl is-active trustsystem-public.service || true
systemctl is-active trustsystem-admin.service || true

echo "=== DEPLOY COMPLETE (SAFE MODE) ==="