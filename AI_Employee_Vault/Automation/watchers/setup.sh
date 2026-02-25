#!/bin/bash

# AI Employee Watchers Setup Script
# Installs dependencies and prepares watchers for production use

cd "$(dirname "$0")"

echo "================================================"
echo "AI Employee Watchers - Setup"
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

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to install Playwright browsers"
    echo "   WhatsApp and LinkedIn watchers may not work"
    echo "   Try manually: playwright install chromium"
else
    echo "✓ Playwright browsers installed"
fi

echo ""

# Create required directories
echo "📁 Creating required directories..."

mkdir -p "../../Needs_Action"
mkdir -p "../../Logs"

echo "✓ Directories created"
echo ""

# Make scripts executable
echo "🔐 Setting executable permissions..."

chmod +x base_watcher.py
chmod +x gmail_watcher.py
chmod +x whatsapp_watcher.py
chmod +x linkedin_watcher.py
chmod +x run_all_watchers.py

echo "✓ Permissions set"
echo ""

# Check for credentials.json (Gmail)
if [ ! -f "../../credentials.json" ]; then
    echo "⚠️  Warning: credentials.json not found"
    echo "   Gmail watcher requires Google API credentials"
    echo "   Place credentials.json in: $(cd ../.. && pwd)/credentials.json"
    echo ""
fi

echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Gmail Watcher Setup:"
echo "   - Obtain credentials.json from Google Cloud Console"
echo "   - Place in project root: ../../credentials.json"
echo "   - Run: python3 gmail_watcher.py"
echo "   - Complete OAuth flow in browser"
echo ""
echo "2. WhatsApp Watcher Setup:"
echo "   - Run: python3 whatsapp_watcher.py"
echo "   - Scan QR code with phone"
echo "   - Session will be saved"
echo ""
echo "3. LinkedIn Watcher Setup:"
echo "   - Run: python3 linkedin_watcher.py"
echo "   - Login manually in browser"
echo "   - Session will be saved"
echo ""
echo "4. Run All Watchers:"
echo "   - Run: python3 run_all_watchers.py"
echo "   - All watchers will run continuously"
echo ""
echo "For detailed documentation, see README.md"
