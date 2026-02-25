#!/bin/bash
# Gmail Watcher Skill - Installation & Test Script

echo "📧 Gmail Watcher Skill - Setup & Test"
echo "======================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "✗ Node.js not found. Please install Node.js first."
    exit 1
fi
echo "✓ Node.js found: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "✗ npm not found. Please install npm first."
    exit 1
fi
echo "✓ npm found: $(npm --version)"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 not found. Please install Python3 first."
    exit 1
fi
echo "✓ Python3 found: $(python3 --version)"

# Check credentials.json
if [ ! -f "credentials.json" ]; then
    echo "✗ credentials.json not found in vault root"
    echo "  Download OAuth credentials from Google Cloud Console"
    exit 1
fi
echo "✓ credentials.json found"

# Check googleapis package
if [ ! -d "node_modules/googleapis" ]; then
    echo "⚠ googleapis package not found"
    echo "  Installing googleapis..."
    npm install googleapis
    if [ $? -eq 0 ]; then
        echo "✓ googleapis installed successfully"
    else
        echo "✗ Failed to install googleapis"
        exit 1
    fi
else
    echo "✓ googleapis package found"
fi

# Check append_log.py
if [ ! -f "Skills/process_needs_action/append_log.py" ]; then
    echo "✗ append_log.py not found"
    exit 1
fi
echo "✓ append_log.py found"

# Check directories
for dir in "Needs_Action" "Logs"; do
    if [ ! -d "$dir" ]; then
        echo "✗ Directory not found: $dir"
        exit 1
    fi
done
echo "✓ Required directories exist"

# Check skill files
echo ""
echo "Skill Files:"
echo "------------"
ls -lh Skills/gmail_watcher_skill/

echo ""
echo "✅ Setup complete! Ready to run."
echo ""
echo "Next steps:"
echo "1. Run: node Skills/gmail_watcher_skill/gmail_watcher.js"
echo "2. Authorize the app (first time only)"
echo "3. Check Needs_Action/ for new email files"
echo ""
