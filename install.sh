#!/bin/bash
set -euo pipefail

echo "=== TrustSystem Installer ==="

PROJECT_DIR="/opt/trustsystem"

# -------------------------
# DEPENDENCIES
# -------------------------
echo "[1/7] Installing dependencies..."

export DEBIAN_FRONTEND=noninteractive

apt update -y
apt install -y python3 python3-venv python3-pip git curl ca-certificates

# -------------------------
# REPO
# -------------------------
echo "[2/7] Repository..."

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "[INFO] Updating repo..."
    cd "$PROJECT_DIR"
    git fetch --all
    git reset --hard origin/main
    git pull
else
    echo "[INFO] Cloning repo..."
    rm -rf "$PROJECT_DIR"
    git clone https://github.com/danilwarhammer40000/trustsystem.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# -------------------------
# VENV
# -------------------------
echo "[3/7] Python env..."

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# -------------------------
# CONFIG
# -------------------------
echo "[4/7] Configuration..."

ENV_FILE="$PROJECT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    echo ""
    echo "⚠️ .env already exists"
    echo "1) Rewrite config"
    echo "2) Keep current"
    echo "3) Exit"
    read -r -p "Choose: " CHOICE

    case "$CHOICE" in
        1) ;;
        2) ;;
        3) exit 0 ;;
        *) exit 1 ;;
    esac
fi

if [ ! -f "$ENV_FILE" ] || [ "${CHOICE:-1}" = "1" ]; then

    read -r -p "ADMIN_BOT_TOKEN: " ADMIN_BOT_TOKEN
    read -r -p "PUBLIC_BOT_TOKEN: " PUBLIC_BOT_TOKEN
    read -r -p "ADMIN_TG_ID: " ADMIN_TG_ID
    read -r -p "DOMAIN: " DOMAIN

    cat > "$ENV_FILE" <<EOF
ADMIN_BOT_TOKEN=$ADMIN_BOT_TOKEN
PUBLIC_BOT_TOKEN=$PUBLIC_BOT_TOKEN
ADMIN_TG_ID=$ADMIN_TG_ID
DOMAIN=$DOMAIN
PYTHONPATH=$PROJECT_DIR
EOF

    chmod 600 "$ENV_FILE"
fi

# -------------------------
# SYSTEMD INSTALL
# -------------------------
echo "[5/7] Installing systemd..."

install_unit () {
    local name=$1
    local src="$PROJECT_DIR/systemd/$name"

    if [ -f "$src" ]; then
        echo "[INFO] Installing $name"
        cp "$src" "/etc/systemd/system/$name"
        chmod 644 "/etc/systemd/system/$name"
        systemctl enable "$name"
    else
        echo "[ERROR] Missing $name"
        exit 1
    fi
}

install_unit "trustsystem-admin.service"
install_unit "trustsystem-public.service"
install_unit "trustsystem-expire.service"
install_unit "trustsystem-expire.timer"

# -------------------------
# START
# -------------------------
echo "[6/7] Starting services..."

systemctl daemon-reload

systemctl restart trustsystem-admin.service
systemctl restart trustsystem-public.service
systemctl start trustsystem-expire.timer

# -------------------------
# STATUS
# -------------------------
echo "[7/7] Status..."

systemctl status trustsystem-admin.service --no-pager || true
systemctl status trustsystem-public.service --no-pager || true

echo ""
echo "Timers:"
systemctl list-timers | grep trustsystem || true

echo ""
echo "DONE"
echo "Logs:"
echo "journalctl -u trustsystem-admin -f"
echo "journalctl -u trustsystem-public -f"
