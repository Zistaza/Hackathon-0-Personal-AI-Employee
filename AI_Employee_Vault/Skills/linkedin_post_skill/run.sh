#!/bin/bash

# LinkedIn Post Skill Runner
# Usage: ./run.sh [generate|process]

cd "$(dirname "$0")"

MODE="${1:-process}"

echo "🔵 LinkedIn Post Skill"
echo "================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

if [ "$MODE" = "generate" ]; then
    echo "📝 Generating new draft..."
    shift
    node index.js generate "$@"
elif [ "$MODE" = "process" ]; then
    echo "🚀 Processing approved posts..."
    node index.js process
else
    echo "❌ Invalid mode: $MODE"
    echo "Usage: ./run.sh [generate|process]"
    exit 1
fi

echo "================================"
echo "✅ LinkedIn Post Skill completed"
