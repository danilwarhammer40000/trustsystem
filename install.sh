#!/bin/bash
set -euo pipefail

echo "=== TrustSystem Installer ==="

PROJECT_DIR="/opt/trustsystem"
REPO_URL="https://github.com/danilwarhammer40000/trustsystem.git"

echo "[0/8] Checking apt lock..."

while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    echo "[INFO] Waiting for apt lock..."
    sleep 5
done

echo "[1/8] Installing dependencies..."

export DEBIAN_FRONTEND=noninteractive

apt update -y
apt install -y python3 python3-venv python3-pip git curl ca-certificates

echo "[2/8] Repository..."

if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
else
    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo "[3/8] Python env..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 👉 YooKassa
pip install yookassa httpx

echo "[4/8] Configuration..."

ENV_FILE="$PROJECT_DIR/.env"

create_env() {
    echo ""

    read -r -p "ADMIN_BOT_TOKEN: " ADMIN_BOT_TOKEN
    read -r -p "PUBLIC_BOT_TOKEN: " PUBLIC_BOT_TOKEN
    read -r -p "ADMIN_TG_ID: " ADMIN_TG_ID
    read -r -p "DOMAIN: " DOMAIN

    echo ""
    echo "=== YooKassa Setup ==="

    read -r -p "YOOKASSA_SHOP_ID: " YOOKASSA_SHOP_ID
    read -r -p "YOOKASSA_API_KEY: " YOOKASSA_API_KEY

    cat > "$ENV_FILE" <<EOF
ADMIN_BOT_TOKEN=$ADMIN_BOT_TOKEN
PUBLIC_BOT_TOKEN=$PUBLIC_BOT_TOKEN
ADMIN_TG_ID=$ADMIN_TG_ID
DOMAIN=$DOMAIN

YOOKASSA_SHOP_ID=$YOOKASSA_SHOP_ID
YOOKASSA_API_KEY=$YOOKASSA_API_KEY

PYTHONPATH=$PROJECT_DIR
EOF

    chmod 600 "$ENV_FILE"
    echo "[OK] .env saved"
}

create_env

echo "[5/8] Installing systemd..."

install_unit () {
    local name=$1
    cp "$PROJECT_DIR/systemd/$name" "/etc/systemd/system/$name"
    chmod 644 "/etc/systemd/system/$name"
}

install_unit "trustsystem-admin.service"
install_unit "trustsystem-public.service"
install_unit "trustsystem-expire.service"
install_unit "trustsystem-expire.timer"

systemctl daemon-reload

systemctl enable trustsystem-admin.service
systemctl enable trustsystem-public.service
systemctl enable trustsystem-expire.timer

echo "[6/8] Starting services..."

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service
systemctl start trustsystem-expire.timer

echo "[7/8] DONE"