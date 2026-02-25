#!/bin/bash
# WhatsApp & LinkedIn Authentication using Windows Chrome
# This script uses Windows Chrome with remote debugging to show the browser

cd "/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault"

echo "=========================================="
echo "WhatsApp & LinkedIn Authentication"
echo "=========================================="
echo ""
echo "We'll use Windows Chrome to authenticate these services."
echo ""

# Find Windows Chrome
CHROME_PATH="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
if [ ! -f "$CHROME_PATH" ]; then
    CHROME_PATH="/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
fi

if [ ! -f "$CHROME_PATH" ]; then
    echo "✗ Chrome not found in standard Windows locations."
    echo "Please install Chrome or update the path in this script."
    exit 1
fi

echo "✓ Found Chrome at: $CHROME_PATH"
echo ""

# Function to authenticate WhatsApp
authenticate_whatsapp() {
    echo "=========================================="
    echo "WhatsApp Authentication"
    echo "=========================================="
    echo ""
    echo "Instructions:"
    echo "  1. Chrome will open with WhatsApp Web"
    echo "  2. Scan the QR code with your phone"
    echo "  3. Wait for your chats to load"
    echo "  4. Close Chrome when done"
    echo ""
    read -p "Press ENTER to open WhatsApp Web in Chrome..."

    USER_DATA_DIR="$(pwd)/Automation/watchers/whatsapp_session"

    echo ""
    echo "Opening WhatsApp Web in Chrome..."
    echo "Keep the window open until your chats load!"
    echo ""

    "$CHROME_PATH" \
        --user-data-dir="$USER_DATA_DIR" \
        --no-first-run \
        --no-default-browser-check \
        "https://web.whatsapp.com" &

    CHROME_PID=$!

    echo "Chrome PID: $CHROME_PID"
    echo ""
    echo "When you're done:"
    echo "  - Close Chrome normally"
    echo "  - Or press Ctrl+C here to continue"
    echo ""

    wait $CHROME_PID 2>/dev/null || true

    echo ""
    echo "✓ WhatsApp authentication complete!"
    echo ""
}

# Function to authenticate LinkedIn
authenticate_linkedin() {
    echo "=========================================="
    echo "LinkedIn Authentication"
    echo "=========================================="
    echo ""
    echo "Instructions:"
    echo "  1. Chrome will open with LinkedIn"
    echo "  2. Log in with your credentials"
    echo "  3. Complete 2FA if required"
    echo "  4. Wait for your feed to load"
    echo "  5. Close Chrome when done"
    echo ""
    read -p "Press ENTER to open LinkedIn in Chrome..."

    USER_DATA_DIR="$(pwd)/Automation/watchers/linkedin_session"

    echo ""
    echo "Opening LinkedIn in Chrome..."
    echo "Keep the window open until your feed loads!"
    echo ""

    "$CHROME_PATH" \
        --user-data-dir="$USER_DATA_DIR" \
        --no-first-run \
        --no-default-browser-check \
        "https://www.linkedin.com" &

    CHROME_PID=$!

    echo "Chrome PID: $CHROME_PID"
    echo ""
    echo "When you're done:"
    echo "  - Close Chrome normally"
    echo "  - Or press Ctrl+C here to continue"
    echo ""

    wait $CHROME_PID 2>/dev/null || true

    echo ""
    echo "✓ LinkedIn authentication complete!"
    echo ""
}

# Main menu
while true; do
    echo ""
    echo "=========================================="
    echo "Select service to authenticate:"
    echo "=========================================="
    echo "1) WhatsApp"
    echo "2) LinkedIn"
    echo "3) Both (WhatsApp then LinkedIn)"
    echo "4) Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            authenticate_whatsapp
            ;;
        2)
            authenticate_linkedin
            ;;
        3)
            authenticate_whatsapp
            authenticate_linkedin
            ;;
        4)
            echo ""
            echo "Done! You can now restart the watchers."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please enter 1-4."
            ;;
    esac
done
