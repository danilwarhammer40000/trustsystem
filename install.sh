#!/bin/bash
set -euo pipefail

echo "=== TrustSystem Installer ==="

PROJECT_DIR="/opt/trustsystem"
REPO_URL="https://github.com/danilwarhammer40000/trustsystem.git"

# -------------------------
# WAIT FOR APT LOCK
# -------------------------
echo "[0/8] Checking apt lock..."

while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    echo "[INFO] Waiting for apt lock..."
    sleep 5
done

# -------------------------
# DEPENDENCIES
# -------------------------
echo "[1/8] Installing dependencies..."

export DEBIAN_FRONTEND=noninteractive

apt update -y
apt install -y python3 python3-venv python3-pip git curl ca-certificates

# -------------------------
# REPO
# -------------------------
echo "[2/8] Repository..."

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Updating repo..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo "[INFO] Cloning repo..."
    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# -------------------------
# VENV
# -------------------------
echo "[3/8] Python env..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 👉 ДОПОЛНИТЕЛЬНО ДЛЯ YOOMONEY
pip install yoomoney httpx

# -------------------------
# CONFIG
# -------------------------
echo "[4/8] Configuration..."

ENV_FILE="$PROJECT_DIR/.env"

is_valid_env() {
    [ -f "$ENV_FILE" ] || return 1
    grep -q "ADMIN_BOT_TOKEN=" "$ENV_FILE" && \
    grep -q "PUBLIC_BOT_TOKEN=" "$ENV_FILE" && \
    grep -q "ADMIN_TG_ID=" "$ENV_FILE" && \
    grep -q "DOMAIN=" "$ENV_FILE"
}

create_env() {
    echo ""

    read -r -p "ADMIN_BOT_TOKEN: " ADMIN_BOT_TOKEN
    read -r -p "PUBLIC_BOT_TOKEN: " PUBLIC_BOT_TOKEN
    read -r -p "ADMIN_TG_ID: " ADMIN_TG_ID
    read -r -p "DOMAIN: " DOMAIN

    echo ""
    echo "=== YooMoney Setup ==="
    read -r -p "YOOMONEY_RECEIVER (кошелек или shopId): " YOOMONEY_RECEIVER
    read -r -p "YOOMONEY_TOKEN (если нет — Enter): " YOOMONEY_TOKEN

    cat > "$ENV_FILE" <<EOF
ADMIN_BOT_TOKEN=$ADMIN_BOT_TOKEN
PUBLIC_BOT_TOKEN=$PUBLIC_BOT_TOKEN
ADMIN_TG_ID=$ADMIN_TG_ID
DOMAIN=$DOMAIN

YOOMONEY_RECEIVER=$YOOMONEY_RECEIVER
YOOMONEY_TOKEN=$YOOMONEY_TOKEN

PYTHONPATH=$PROJECT_DIR
EOF

    chmod 600 "$ENV_FILE"
    echo "[OK] .env saved"
}

if is_valid_env; then
    echo ""
    echo "⚠️ Valid .env detected"
    echo "1) Rewrite config"
    echo "2) Keep current"
    echo "3) Exit"
    read -r -p "Choose: " CHOICE

    case "$CHOICE" in
        1) create_env ;;
        2) echo "[INFO] Keeping config" ;;
        3) exit 0 ;;
        *) echo "Invalid option"; exit 1 ;;
    esac
else
    echo "[INFO] No valid config found"
    create_env
fi

# -------------------------
# SYSTEMD INSTALL
# -------------------------
echo "[5/8] Installing systemd..."

install_unit () {
    local name=$1
    local src="$PROJECT_DIR/systemd/$name"

    if [ ! -f "$src" ]; then
        echo "[ERROR] Missing $name"
        exit 1
    fi

    echo "[INFO] Installing $name"
    cp "$src" "/etc/systemd/system/$name"
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

# -------------------------
# START
# -------------------------
echo "[6/8] Starting services..."

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service
systemctl start trustsystem-expire.timer

# -------------------------
# STATUS
# -------------------------
echo "[7/8] Status..."

systemctl status trustsystem-admin.service --no-pager || true
systemctl status trustsystem-public.service --no-pager || true

echo ""
echo "Timers:"
systemctl list-timers | grep trustsystem || true

echo ""
echo "DONE"
echo ""
echo "Logs:"
echo "journalctl -u trustsystem-admin -f"
echo "journalctl -u trustsystem-public -f"