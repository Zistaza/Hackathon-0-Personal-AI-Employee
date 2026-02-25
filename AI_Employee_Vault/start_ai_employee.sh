#!/bin/bash

cd /mnt/c/Users/"Tesla Laptops"/Desktop/AI_Employee_Vault/AI_Employee_Vault

echo "🚀 Starting AI Employee Orchestrator..."

while true
do
    python3 Skills/integration_orchestrator/index.py
    echo "⚠ Orchestrator crashed. Restarting in 5 seconds..."
    sleep 5
done
