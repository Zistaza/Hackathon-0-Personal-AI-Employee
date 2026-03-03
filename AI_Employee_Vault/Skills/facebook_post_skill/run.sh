#!/bin/bash
# Facebook Post Skill - Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Facebook Post Skill - Enterprise Edition"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if integration_orchestrator exists
ORCHESTRATOR_DIR="../integration_orchestrator"
if [ ! -d "$ORCHESTRATOR_DIR" ]; then
    echo "Error: integration_orchestrator not found at $ORCHESTRATOR_DIR"
    exit 1
fi

# Run the skill
if [ "$1" == "--test" ]; then
    echo "Running in test mode..."
    python3 index.py --test
elif [ -z "$1" ]; then
    echo "Usage: ./run.sh <message> [--media <files>]"
    echo "   or: ./run.sh --test"
    exit 1
else
    python3 index.py "$@"
fi
