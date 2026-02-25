#!/bin/bash

# WhatsApp Watcher Skill Runner
# Usage: ./run.sh

cd "$(dirname "$0")"

echo "🔍 Starting WhatsApp Watcher..."
echo "================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run the watcher
node index.js

echo "================================"
echo "✅ WhatsApp Watcher completed"
