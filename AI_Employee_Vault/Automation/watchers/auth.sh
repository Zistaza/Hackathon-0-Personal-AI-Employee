#!/bin/bash
# Authenticate WhatsApp and LinkedIn using Playwright with WSLg
cd "/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault/Automation/watchers"
source ../../.venv/bin/activate

export DISPLAY=:0

echo "=========================================="
echo "Playwright Browser Authentication"
echo "=========================================="
echo ""
echo "This will open browser windows for authentication."
echo "Make sure you can see GUI windows from WSL."
echo ""

python3 authenticate_playwright.py
