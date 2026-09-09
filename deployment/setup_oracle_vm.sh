#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Infrastructure (OCI) Ampere A1 ARM64 VM Deployment Script
# OS: Ubuntu 24.04 LTS (ARM64 / aarch64)
# Project: AI-Powered Mobile Urban Intelligence Backend
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/AI-Powered-Mobile-Urban-Intelligence"
ENV_FILE="${APP_DIR}/backend/.env"
DB_NAME="urban_intelligence"
DB_USER="urban_app"

echo '=== [1/8] Updating System & Installing Core Dependencies ==='
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    ufw

echo '=== [2/8] Installing & Configuring PostgreSQL (Private 127.0.0.1) ==='
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

# Idempotently check if user and database already exist
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}';" 2>/dev/null || echo "0")
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" 2>/dev/null || echo "0")

if [ "${USER_EXISTS}" = "1" ]; then
    echo "PostgreSQL user '${DB_USER}' already exists. Preserving existing database credentials."
    DB_PASS=""
else
    echo "Creating PostgreSQL user '${DB_USER}'..."
    DB_PASS="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)"
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASS}';"
fi

if [ "${DB_EXISTS}" = "1" ]; then
    echo "PostgreSQL database '${DB_NAME}' already exists."
else
    echo "Creating PostgreSQL database '${DB_NAME}'..."
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
fi

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" >/dev/null 2>&1 || true
sudo -u postgres psql -d ${DB_NAME} -c "GRANT ALL ON SCHEMA public TO ${DB_USER};" >/dev/null 2>&1 || true

echo '=== [3/8] Installing Caddy Web Server (Automated HTTPS Reverse Proxy) ==='
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg --yes
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

echo '=== [4/8] Setting Up Application Directory & Virtual Environment ==='
if [ ! -d "${APP_DIR}" ]; then
    sudo git clone https://github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence.git "${APP_DIR}"
    sudo chown -R ubuntu:ubuntu "${APP_DIR}"
else
    cd "${APP_DIR}"
    sudo -u ubuntu git fetch origin
    sudo -u ubuntu git checkout main
    sudo -u ubuntu git pull origin main
fi

cd "${APP_DIR}/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo '=== [5/8] Creating Production Environment Configuration ==='
if [ -f "${ENV_FILE}" ]; then
    echo "Existing production .env found at ${ENV_FILE}. Preserving existing configuration."
else
    if [ -z "${DB_PASS}" ]; then
        # In case user existed before script ran but .env was missing, generate a new password and set it
        DB_PASS="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)"
        sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASS}';"
    fi
    cat <<ENVEOF > "${ENV_FILE}"
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}
DEBUG=false
AUTO_SEED=true
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ai-powered-mobile-urban-intelligenc.vercel.app
MIN_CONFIDENCE=0.65
DETECTION_FPS_POTHOLE=5.0
DETECTION_FPS_TRAFFIC=5.0
INFERENCE_CONFIDENCE=0.25
INFERENCE_CONFIDENCE_POTHOLE=0.45
INFERENCE_IOU=0.45
YOLO_POTHOLE_WEIGHTS=edge-ai/pothole-latest/Pothole_Road_Condition_Model/best_2.pt
YOLO_TRAFFIC_WEIGHTS=yolov8n.pt
ENVEOF
    chmod 600 "${ENV_FILE}"
    echo "Created production .env file (permissions: 0600, secrets masked)."
fi

echo '=== [6/8] Installing & Starting Systemd Service ==='
sudo cp "${APP_DIR}/deployment/urban-intelligence.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now urban-intelligence
sudo systemctl status urban-intelligence --no-pager

echo '=== [7/8] Configuring Caddy Reverse Proxy ==='
sudo cp "${APP_DIR}/deployment/Caddyfile" /etc/caddy/Caddyfile
sudo systemctl restart caddy
sudo systemctl status caddy --no-pager

echo '=== [8/8] Hardening Linux UFW Firewall ==='
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH (manage your VM)
sudo ufw allow 80/tcp   # HTTP (Caddy ACME validation & redirect)
sudo ufw allow 443/tcp  # HTTPS (Public API, WebSockets, Range Streaming)
sudo ufw --force enable

echo '=============================================================================='
echo ' Deployment Complete!'
echo " Database: postgresql://${DB_USER}:***@127.0.0.1:5432/${DB_NAME}"
echo ' Public ports open: 22 (SSH), 80 (HTTP), 443 (HTTPS)'
echo ' Private ports protected: 8000 (FastAPI), 5432 (PostgreSQL)'
echo '=============================================================================='
