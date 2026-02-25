#!/bin/bash

# WhatsApp Watcher Skill Setup Script
# Installs dependencies and prepares the skill for first run

cd "$(dirname "$0")"

echo "🔧 WhatsApp Watcher Skill Setup"
echo "================================"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is required but not installed"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js found: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not installed"
    exit 1
fi

echo "✓ npm found: $(npm --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Create required directories
echo ""
echo "📁 Creating required directories..."

mkdir -p "../../Needs_Action"
mkdir -p "../../Logs"
mkdir -p "./whatsapp_session"

echo "✓ Directories created"

# Initialize processed_ids.json if it doesn't exist
if [ ! -f "processed_ids.json" ]; then
    echo "[]" > processed_ids.json
    echo "✓ Created processed_ids.json"
fi

# Make run.sh executable
chmod +x run.sh

echo ""
echo "================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./run.sh"
echo "2. Scan QR code when prompted"
echo "3. Session will be saved for future runs"
echo ""
echo "To schedule automatic runs:"
echo "  crontab -e"
echo "  Add: */5 * * * * cd $(pwd) && ./run.sh"
