#!/bin/bash

# LinkedIn Post Skill Setup Script
# Installs dependencies and prepares the skill for first run

cd "$(dirname "$0")"

echo "🔧 LinkedIn Post Skill Setup"
echo "============================"

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

mkdir -p "../../Pending_Approval"
mkdir -p "../../Posted"
mkdir -p "../../Logs"
mkdir -p "./linkedin_session"

echo "✓ Directories created"

# Check for Company_Handbook.md
if [ ! -f "../../Company_Handbook.md" ]; then
    echo ""
    echo "⚠️  Warning: Company_Handbook.md not found"
    echo "   The skill will use generic professional tone"
    echo "   Create Company_Handbook.md in the root directory for brand voice matching"
fi

# Make run.sh executable
chmod +x run.sh

echo ""
echo "============================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "To generate a draft:"
echo "  node index.js generate \"Your Topic\" \"Key point 1\" \"Key point 2\""
echo ""
echo "To review and approve:"
echo "  1. Open draft in ../../Pending_Approval/"
echo "  2. Edit content if needed"
echo "  3. Change status to 'approved'"
echo ""
echo "To post approved drafts:"
echo "  ./run.sh"
echo "  (You'll need to login to LinkedIn on first run)"
echo ""
echo "To test without posting:"
echo "  1. Edit config.json and set \"dryRun\": true"
echo "  2. Run: ./run.sh"
