#!/bin/bash
set -euo pipefail

echo "=== TrustSystem Production Installer (fixed) ==="

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

echo "[3/9] Clone repository..."
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
else
    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

echo "[4/9] Main venv..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel

# СТАВИМ ТОЛЬКО requirements (без перетирания)
pip install -r requirements.txt

# доп зависимости (если их нет в requirements)
pip install yookassa httpx redis

deactivate

echo "[5/9] Webhook venv..."
WEBHOOK_DIR="$PROJECT_DIR/webhook_service"

mkdir -p "$WEBHOOK_DIR"

if [ ! -d "$WEBHOOK_DIR/venv" ]; then
    python3 -m venv "$WEBHOOK_DIR/venv"
fi

source "$WEBHOOK_DIR/venv/bin/activate"

pip install --upgrade pip
pip install fastapi uvicorn httpx redis yookassa

deactivate

echo "[6/9] ENV setup..."

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

install_service () {
    if [ -f "$PROJECT_DIR/systemd/$1" ]; then
        cp "$PROJECT_DIR/systemd/$1" "/etc/systemd/system/$1"
        chmod 644 "/etc/systemd/system/$1"
        systemctl enable "$1"
        echo "[OK] $1 installed"
    else
        echo "[SKIP] $1 not found"
    fi
}

install_service trustsystem-admin.service
install_service trustsystem-public.service
install_service trustsystem-expire.service
install_service trustsystem-expire.timer
install_service trustsystem-webhook.service
install_service trusttunnel.service

systemctl daemon-reload

echo "[8/9] Restart services..."

systemctl restart redis-server

systemctl restart trustsystem-admin.service || true
systemctl restart trustsystem-public.service || true
systemctl restart trustsystem-webhook.service || true

echo "[9/9] DONE"
echo "Check logs:"
echo "journalctl -u trustsystem-webhook -f"