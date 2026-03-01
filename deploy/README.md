# BNB Banking Agents — Deployment Guide

## Azure VM Deployment

The demo runs on an Azure VM (`copilotcli`) in Sweden Central with the following stack:

- **Backend:** FastAPI + Uvicorn (Python 3.12) on port 8000
- **Dashboard:** React SPA served via Nginx
- **Reverse Proxy:** Nginx with Let's Encrypt SSL
- **URL:** `https://135-116-65-177.sslip.io`

## Setup Steps

### 1. Clone & Install

```bash
cd /home/admin
git clone https://github.com/prateem_microsoft/bnb-banking-agents.git
cd bnb-banking-agents
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Build Dashboard

```bash
cd dashboard
npm install
npm run build
cd ..
```

### 3. Configure Systemd Service

```bash
# Copy and edit the service file — replace placeholder values with real secrets
sudo cp deploy/bnb-backend.service /etc/systemd/system/
sudo vi /etc/systemd/system/bnb-backend.service
# Set: WHATSAPP_CHANNEL_ID and ACS_CONNECTION_STRING

sudo systemctl daemon-reload
sudo systemctl enable bnb-backend
sudo systemctl start bnb-backend
```

### 4. Configure Nginx

```bash
sudo cp deploy/nginx-site.conf /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d 135-116-65-177.sslip.io
```

### 6. Fix Dashboard Permissions

```bash
chmod o+x /home/admin
chmod o+x /home/admin/bnb-banking-agents
chmod o+x /home/admin/bnb-banking-agents/dashboard
chmod -R o+r /home/admin/bnb-banking-agents/dashboard/build
find /home/admin/bnb-banking-agents/dashboard/build -type d -exec chmod o+x {} \;
```

## Azure Resources Required

| Resource | Name | Purpose |
|----------|------|---------|
| Azure OpenAI | `bnb-openai` | GPT-4o for intent classification & agent reasoning |
| Cosmos DB | `bnb-cosmos-db2026` | Customer data, transactions, agent state |
| ACS | `wapp` | WhatsApp Business via Advanced Messaging |
| Speech Service | `bnb-speech` | Hindi/English STT/TTS for voice agents |
| Document Intelligence | `bnb-docint` | Aadhaar/PAN document OCR |
| SignalR | `bnb-signalr` | Real-time dashboard event streaming |
| Key Vault | `bnb-poc-kv` | Secret management |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (e.g., `gpt-4o`) |
| `COSMOS_ENDPOINT` | Cosmos DB endpoint |
| `COSMOS_DATABASE` | Cosmos DB database name |
| `ACS_CONNECTION_STRING` | Azure Communication Services connection string |
| `WHATSAPP_CHANNEL_ID` | WhatsApp channel registration ID from ACS portal |
| `DATAVERSE_URL` | Dataverse/Dynamics 365 URL for Copilot Studio |
| `AZURE_TENANT_ID` | Azure AD tenant ID |

## Verify Deployment

```bash
# Health check
curl https://135-116-65-177.sslip.io/api/health

# List agents
curl https://135-116-65-177.sslip.io/api/agents

# Test onboarding scenario
curl -X POST https://135-116-65-177.sslip.io/api/chat \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-001-ANANYA","message":"Hi, I want to open a bank account","channel":"whatsapp"}'
```
