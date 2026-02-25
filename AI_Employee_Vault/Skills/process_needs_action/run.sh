#!/bin/bash

# Process Needs Action Skill v2.0 Runner
# Processes files in /Needs_Action with enhanced planning and risk analysis

cd "$(dirname "$0")"

echo "📋 Process Needs Action Skill v2.0"
echo "===================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    exit 1
fi

# Run the skill
echo "🔍 Scanning /Needs_Action directory..."
python3 process_needs_action.py

EXIT_CODE=$?

echo "===================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Process Needs Action completed successfully"
else
    echo "⚠️  Process Needs Action completed with errors"
fi

exit $EXIT_CODE
