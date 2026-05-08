#!/bin/bash
set -euo pipefail

echo "=== TrustSystem Production Installer (final) ==="

PROJECT_DIR="/opt/trustsystem"
REPO_URL="https://github.com/danilwarhammer40000/trustsystem.git"

echo "[0/9] Waiting apt lock..."
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    echo "[INFO] apt locked, waiting..."
    sleep 3
done

export DEBIAN_FRONTEND=noninteractive

echo "[1/9] System packages..."
apt update -y
apt install -y \
    python3 python3-venv python3-pip git curl ca-certificates \
    redis-server build-essential

echo "[2/9] Enable Redis..."
systemctl enable redis-server
systemctl restart redis-server

echo "[3/9] Repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
else
    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo "[4/9] Main venv..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# ВСЕ зависимости в один venv (включая webhook)
pip install yookassa httpx redis fastapi uvicorn aiogram

deactivate


echo "[6/9] Configuration..."

ENV_FILE="$PROJECT_DIR/.env"

echo ""
read -r -p "ADMIN_BOT_TOKEN: " ADMIN_BOT_TOKEN
read -r -p "PUBLIC_BOT_TOKEN: " PUBLIC_BOT_TOKEN
read -r -p "ADMIN_TG_ID: " ADMIN_TG_ID
read -r -p "DOMAIN: " DOMAIN

echo ""
echo "=== YooKassa ==="

read -r -p "YOOKASSA_SHOP_ID: " YOOKASSA_SHOP_ID
read -r -p "YOOKASSA_API_KEY: " YOOKASSA_API_KEY

cat > "$ENV_FILE" <<EOF
PYTHONPATH=$PROJECT_DIR

ADMIN_BOT_TOKEN=$ADMIN_BOT_TOKEN
PUBLIC_BOT_TOKEN=$PUBLIC_BOT_TOKEN
ADMIN_TG_ID=$ADMIN_TG_ID
DOMAIN=$DOMAIN

YOOKASSA_SHOP_ID=$YOOKASSA_SHOP_ID
YOOKASSA_API_KEY=$YOOKASSA_API_KEY

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
EOF

chmod 600 "$ENV_FILE"
echo "[OK] .env saved"

echo "[7/9] Systemd services..."

install_unit () {
    cp "$PROJECT_DIR/systemd/$1" "/etc/systemd/system/$1"
    chmod 644 "/etc/systemd/system/$1"
}

# services
install_unit trustsystem-admin.service
install_unit trustsystem-public.service
install_unit trustsystem-expire.service
install_unit trustsystem-webhook.service
install_unit trustsystem-sync.service

# timers
install_unit trustsystem-expire.timer
install_unit trustsystem-sync.timer

systemctl daemon-reload

# enable services
systemctl enable trustsystem-admin.service
systemctl enable trustsystem-public.service
systemctl enable trustsystem-expire.service
systemctl enable trustsystem-webhook.service
systemctl enable trustsystem-sync.service

# enable timers
systemctl enable trustsystem-expire.timer
systemctl enable trustsystem-sync.timer

echo "[8/9] Starting services..."

systemctl restart redis-server

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service
systemctl restart trustsystem-webhook.service
systemctl restart trustsystem-sync.service

# timers запускаются через start
systemctl start trustsystem-expire.timer
systemctl start trustsystem-sync.timer

echo "[9/9] Status report"

echo ""
echo "=== SERVICES ==="
systemctl status trustsystem-admin.service --no-pager || true
systemctl status trustsystem-public.service --no-pager || true
systemctl status trustsystem-webhook.service --no-pager || true
systemctl status trustsystem-sync.service --no-pager || true

echo ""
echo "=== TIMERS ==="
systemctl list-timers | grep trustsystem || true

echo ""
echo "=== REDIS ==="
systemctl status redis-server --no-pager || true

echo ""
echo "=== DONE ==="
echo "Logs:"
echo "journalctl -u trustsystem-webhook -f"