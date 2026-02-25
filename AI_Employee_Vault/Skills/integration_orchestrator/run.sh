#!/bin/bash

# Integration Orchestrator Runner
# Simple script to start the orchestrator

cd "$(dirname "$0")"

echo "🚀 Starting Integration Orchestrator..."
echo ""

# Check if already running
if pgrep -f "python3 index.py" > /dev/null; then
    echo "⚠️  Orchestrator is already running"
    echo ""
    echo "To stop it:"
    echo "  pkill -f 'python3 index.py'"
    echo ""
    echo "To view logs:"
    echo "  tail -f ../../Logs/integration_orchestrator.log"
    exit 1
fi

# Check dependencies
if ! python3 -c "import watchdog" 2>/dev/null; then
    echo "❌ Dependencies not installed"
    echo "   Run: ./setup.sh"
    exit 1
fi

# Start orchestrator
python3 index.py
