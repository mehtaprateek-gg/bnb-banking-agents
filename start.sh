#!/bin/bash
# BNB Banking Agents - VM Startup Script
set -e

PROJECT_DIR=~/bnb-banking-agents
cd "PROJECT_DIR"

# Activate Python venv
source .venv/bin/activate

# Azure login with managed identity
az login --identity --allow-no-subscriptions 2>/dev/null

# Set environment variables
export PYTHONPATH="PROJECT_DIR"
export AZURE_OPENAI_ENDPOINT="https://bnb-openai.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
export DATAVERSE_URL="https://org8973c330.crm.dynamics.com"
export COSMOS_ENDPOINT="https://bnb-cosmos-db2026.documents.azure.com:443/"
export COSMOS_DATABASE="bnb-db"
export AZURE_TENANT_ID="b2e62839-cc6c-4e1e-8c4a-bc35ebc9b3d9"

echo "[BNB] Starting backend on port 8000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

echo "[BNB] Starting dashboard on port 3000..."
cd dashboard
HOST=0.0.0.0 npx react-scripts start &

echo "[BNB] All services started!"
echo "  Backend:   http://\49.36.114.120:8000"
echo "  Dashboard: http://\49.36.114.120:3000"
wait
