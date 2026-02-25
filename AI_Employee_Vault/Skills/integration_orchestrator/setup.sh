#!/bin/bash

# Integration Orchestrator Setup Script
# Installs dependencies and prepares the orchestrator

cd "$(dirname "$0")"

echo "================================================"
echo "Integration Orchestrator - Setup"
echo "================================================"
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "   Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is required but not installed"
    exit 1
fi

echo "✓ pip3 found: $(pip3 --version)"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo "✓ Python dependencies installed"
echo ""

# Verify directory structure
echo "📁 Verifying directory structure..."

BASE_DIR="$(cd ../.. && pwd)"

REQUIRED_DIRS=(
    "$BASE_DIR/Inbox"
    "$BASE_DIR/Needs_Action"
    "$BASE_DIR/Pending_Approval"
    "$BASE_DIR/Done"
    "$BASE_DIR/Logs"
    "$BASE_DIR/Skills"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "⚠️  Creating missing directory: $dir"
        mkdir -p "$dir"
    fi
done

echo "✓ Directory structure verified"
echo ""

# Check for required skills
echo "🔍 Checking for required skills..."

REQUIRED_SKILLS=(
    "$BASE_DIR/Skills/process_needs_action"
    "$BASE_DIR/Skills/linkedin_post_skill"
)

MISSING_SKILLS=0

for skill in "${REQUIRED_SKILLS[@]}"; do
    if [ ! -d "$skill" ]; then
        echo "⚠️  Warning: Skill not found: $(basename $skill)"
        MISSING_SKILLS=$((MISSING_SKILLS + 1))
    else
        echo "✓ Found: $(basename $skill)"
    fi
done

if [ $MISSING_SKILLS -gt 0 ]; then
    echo ""
    echo "⚠️  Some skills are missing. Orchestrator will work but may not trigger all actions."
fi

echo ""

# Make scripts executable
echo "🔐 Setting executable permissions..."

chmod +x index.py

echo "✓ Permissions set"
echo ""

# Initialize state file
if [ ! -f "processed_events.json" ]; then
    echo "{}" > processed_events.json
    echo "✓ Created processed_events.json"
fi

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Ensure watchers are running:"
echo "   cd ../../Automation/watchers"
echo "   python3 run_all_watchers.py &"
echo ""
echo "2. Start orchestrator:"
echo "   python3 index.py"
echo ""
echo "3. Test the system:"
echo "   - Create a test file in Inbox/"
echo "   - Watch logs: tail -f ../../Logs/integration_orchestrator.log"
echo ""
echo "For detailed documentation, see README.md"
