#!/bin/bash

# Process Needs Action Skill Setup Script
# Prepares the skill for first run

cd "$(dirname "$0")"

echo "🔧 Process Needs Action Skill v2.0 Setup"
echo "========================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "   Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create required directories
echo ""
echo "📁 Creating required directories..."

mkdir -p "../../Needs_Action"
mkdir -p "../../Plans"
mkdir -p "../../Pending_Approval"
mkdir -p "../../Done"
mkdir -p "../../Logs"

echo "✓ Directories created"

# Make scripts executable
echo ""
echo "🔐 Setting executable permissions..."

chmod +x run.sh
chmod +x process_needs_action.py
chmod +x append_log.sh
chmod +x append_log.py

echo "✓ Permissions set"

# Check for jq (required for bash logging)
if ! command -v jq &> /dev/null; then
    echo ""
    echo "⚠️  Warning: jq is not installed"
    echo "   jq is required for bash logging (append_log.sh)"
    echo "   Install with: sudo apt-get install jq (Ubuntu/Debian)"
    echo "   or: brew install jq (macOS)"
    echo ""
    echo "   Python logging (append_log.py) will still work"
fi

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "To process files in /Needs_Action:"
echo "  ./run.sh"
echo ""
echo "The skill will:"
echo "  1. Read files from /Needs_Action"
echo "  2. Analyze content and generate comprehensive plans"
echo "  3. Create plans with risk analysis and approval workflow"
echo "  4. Save plans to /Plans and /Pending_Approval"
echo "  5. Log all activity to /Logs"
echo "  6. Move processed files to /Done"
echo ""
echo "To test:"
echo "  1. Create a test file in ../../Needs_Action/"
echo "  2. Run: ./run.sh"
echo "  3. Check ../../Plans/ for generated plan"
echo "  4. Check ../../Pending_Approval/ for review copy"
echo "  5. Check ../../Done/ for processed file"
echo ""
echo "For automated processing, add to crontab:"
echo "  crontab -e"
echo "  Add: 0 * * * * cd $(pwd) && ./run.sh"
