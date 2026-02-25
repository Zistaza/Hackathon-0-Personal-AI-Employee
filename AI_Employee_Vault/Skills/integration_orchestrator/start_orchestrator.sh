#!/bin/bash
# Quick Start Script for Enhanced Orchestrator with Email Approval

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     AI EMPLOYEE - EMAIL APPROVAL WORKFLOW QUICK START       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if orchestrator is already running
if pgrep -f "python3.*index.py" > /dev/null; then
    echo "⚠️  Orchestrator is already running"
    echo ""
    echo "To stop it:"
    echo "  pkill -f 'python3.*index.py'"
    echo ""
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import watchdog" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependency: watchdog"
    echo "   Install with: pip install watchdog"
    exit 1
fi

echo "✓ Dependencies OK"
echo ""

# Show current status
echo "Current Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PENDING=$(ls -1 ../../Pending_Approval/email/*.md 2>/dev/null | wc -l)
APPROVED=$(ls -1 ../../Approved/*.md 2>/dev/null | wc -l)
REJECTED=$(ls -1 ../../Rejected/*.md 2>/dev/null | wc -l)
DONE=$(ls -1 ../../Done/*.md 2>/dev/null | wc -l)

echo "  Pending Approval: $PENDING"
echo "  Approved:         $APPROVED"
echo "  Rejected:         $REJECTED"
echo "  Done:             $DONE"
echo ""

# Start orchestrator
echo "Starting Enhanced Orchestrator..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 index.py
