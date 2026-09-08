# Oracle Cloud Infrastructure (OCI) Ampere A1 ARM64 Deployment Guide

This guide details the deployment of the **AI-Powered Mobile Urban Intelligence Platform** backend to an **Oracle Cloud Infrastructure (OCI) Ampere A1 Always-Free VM** (ARM64 / aarch64) connected to the **Vercel React Frontend**.

---

## 1. System Architecture

```
Vercel React Frontend (https://ai-powered-mobile-urban-intelligenc.vercel.app)
       │
       │ HTTPS REST & WSS WebSockets (Port 443)
       ▼
Oracle Cloud ARM64 Always-Free VM (Ubuntu 24.04 LTS / aarch64)
       │
       ├── Caddy Web Server (:80, :443)  ← Auto Let's Encrypt TLS / Reverse Proxy
       │       │
       │       ▼ (127.0.0.1:8000)
       ├── FastAPI Backend (systemd: urban-intelligence.service)
       │       │
       │       ├── YOLOv8 Traffic AI (COCO 80-class vehicle detection)
       │       ├── YOLOv8 Pothole AI (best_2.pt custom road-damage model)
       │       ├── WebSocket Real-time Ingestion & Telemetry Broadcaster
       │       └── Video Stream Engine (HTTP 206 Partial Range Requests)
       │
       └── PostgreSQL 16 (127.0.0.1:5432)  ← Private local database
```

---

## 2. Oracle VM Specifications & Ingress Rules

- **Compute Shape**: `VM.Standard.A1.Flex` (Ampere Altra ARM64)
- **Resources**: 2 OCPU, 12 GB RAM
- **Operating System**: Ubuntu 24.04 LTS ARM64 (`aarch64`)

### OCI Security List / Ingress Rules:

| Protocol | Source CIDR | Port Range | Purpose |
|---|---|---|---|
| **TCP** | `0.0.0.0/0` | `22` | SSH Management |
| **TCP** | `0.0.0.0/0` | `80` | HTTP (Caddy ACME Challenge & Auto-Redirect) |
| **TCP** | `0.0.0.0/0` | `443` | HTTPS (Secure REST API, WSS WebSockets, Video Streaming) |

> **IMPORTANT**: Ports `8000` (FastAPI) and `5432` (PostgreSQL) must **NEVER** be opened in the OCI Security List. They are bound strictly to `127.0.0.1` inside the VM.

---

## 3. Automated One-Command Provisioning

1. **Connect to your Oracle VM**:
   ```bash
   ssh -i ~/.ssh/id_rsa ubuntu@<YOUR_ORACLE_PUBLIC_IP>
   ```

2. **Clone the repository and run the setup script**:
   ```bash
   git clone https://github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence.git /opt/AI-Powered-Mobile-Urban-Intelligence
   cd /opt/AI-Powered-Mobile-Urban-Intelligence/deployment
   chmod +x setup_oracle_vm.sh
   ./setup_oracle_vm.sh
   ```

---

## 4. Manual Configuration Steps

### A. Set Your Public Domain in Caddy
Edit `/etc/caddy/Caddyfile`:
```caddy
api.yourdomain.com {
    reverse_proxy 127.0.0.1:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    encode zstd gzip
}
```
Restart Caddy:
```bash
sudo systemctl restart caddy
```

### B. Verify Application Status
```bash
sudo systemctl status urban-intelligence
sudo journalctl -u urban-intelligence -f
```

---

## 5. Vercel Frontend Configuration

1. Open your project on [Vercel Dashboard](https://vercel.com).
2. Go to **Settings** → **Environment Variables**.
3. Add / Update:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://api.yourdomain.com`
4. Trigger a **Redeploy** on Vercel.

---

## 6. End-to-End Verification

Run the automated verification suite from your local machine or from within the VM:
```bash
python3 deployment/verify_deployment.py --url https://api.yourdomain.com
```
