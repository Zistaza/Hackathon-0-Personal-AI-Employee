#!/bin/bash
# Authentication Helper Script
# This script helps you authenticate each watcher one by one

cd "/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault"
source .venv/bin/activate

echo "=========================================="
echo "Watcher Authentication Helper"
echo "=========================================="
echo ""
echo "This script will help you authenticate each watcher."
echo "Follow the prompts for each service."
echo ""

# Function to authenticate Gmail
authenticate_gmail() {
    echo "=========================================="
    echo "1. GMAIL AUTHENTICATION"
    echo "=========================================="
    echo ""
    echo "What will happen:"
    echo "  1. A browser window will open automatically"
    echo "  2. Sign in with your Google account"
    echo "  3. Grant permissions to access Gmail"
    echo "  4. The browser will show 'Authentication successful'"
    echo "  5. Token will be saved to: Automation/watchers/gmail_token.pickle"
    echo ""
    read -p "Press ENTER to start Gmail authentication..."

    cd Automation/watchers
    python3 -c "
import sys
sys.path.insert(0, '.')
from gmail_watcher import GmailWatcher

print('Initializing Gmail watcher...')
watcher = GmailWatcher(
    credentials_file='../../credentials.json',
    token_file='./gmail_token.pickle'
)
print('Gmail authentication complete!')
print('Token saved successfully.')
"
    cd ../..

    if [ -f "Automation/watchers/gmail_token.pickle" ]; then
        echo ""
        echo "✓ Gmail authentication successful!"
        echo "✓ Token saved to: Automation/watchers/gmail_token.pickle"
        return 0
    else
        echo ""
        echo "✗ Gmail authentication failed or cancelled"
        return 1
    fi
}

# Function to authenticate WhatsApp
authenticate_whatsapp() {
    echo ""
    echo "=========================================="
    echo "2. WHATSAPP AUTHENTICATION"
    echo "=========================================="
    echo ""
    echo "What will happen:"
    echo "  1. A Chrome browser window will open"
    echo "  2. WhatsApp Web will load with a QR code"
    echo "  3. Open WhatsApp on your phone"
    echo "  4. Tap 'Linked Devices' → 'Link a Device'"
    echo "  5. Scan the QR code shown in the browser"
    echo "  6. Wait for WhatsApp to load your chats"
    echo "  7. Session will be saved automatically"
    echo ""
    echo "IMPORTANT: Keep the browser window open until you see your chats!"
    echo ""
    read -p "Press ENTER to start WhatsApp authentication..."

    echo ""
    echo "Opening WhatsApp Web..."
    echo "The browser will stay open for 60 seconds to complete authentication."
    echo "If you need more time, you can run this script again."
    echo ""

    cd Automation/watchers
    timeout 60 python3 -c "
import sys
import asyncio
sys.path.insert(0, '.')
from whatsapp_watcher import WhatsAppWatcher

async def auth():
    print('Initializing WhatsApp watcher...')
    watcher = WhatsAppWatcher(
        user_data_dir='./whatsapp_session',
        headless=False
    )
    print('Opening WhatsApp Web...')
    print('Please scan the QR code with your phone.')
    print('Waiting 60 seconds for authentication...')
    await asyncio.sleep(60)
    print('Closing browser...')

asyncio.run(auth())
" || echo "Timeout reached or interrupted"
    cd ../..

    if [ -d "Automation/watchers/whatsapp_session" ]; then
        echo ""
        echo "✓ WhatsApp session directory created!"
        echo "✓ Session saved to: Automation/watchers/whatsapp_session/"
        echo ""
        echo "Note: If you didn't complete the QR scan, run this script again."
        return 0
    else
        echo ""
        echo "✗ WhatsApp authentication incomplete"
        return 1
    fi
}

# Function to authenticate LinkedIn
authenticate_linkedin() {
    echo ""
    echo "=========================================="
    echo "3. LINKEDIN AUTHENTICATION"
    echo "=========================================="
    echo ""
    echo "What will happen:"
    echo "  1. A Chrome browser window will open"
    echo "  2. LinkedIn login page will load"
    echo "  3. Enter your LinkedIn email and password"
    echo "  4. Complete any 2FA if required"
    echo "  5. Wait until you see your LinkedIn feed"
    echo "  6. Session will be saved automatically"
    echo ""
    echo "IMPORTANT: Keep the browser window open until you see your feed!"
    echo ""
    read -p "Press ENTER to start LinkedIn authentication..."

    echo ""
    echo "Opening LinkedIn..."
    echo "The browser will stay open for 60 seconds to complete authentication."
    echo "If you need more time, you can run this script again."
    echo ""

    cd Automation/watchers
    timeout 60 python3 -c "
import sys
import asyncio
sys.path.insert(0, '.')
from linkedin_watcher import LinkedInWatcher

async def auth():
    print('Initializing LinkedIn watcher...')
    watcher = LinkedInWatcher(
        user_data_dir='./linkedin_session',
        headless=False
    )
    print('Opening LinkedIn...')
    print('Please log in with your credentials.')
    print('Waiting 60 seconds for authentication...')
    await asyncio.sleep(60)
    print('Closing browser...')

asyncio.run(auth())
" || echo "Timeout reached or interrupted"
    cd ../..

    if [ -d "Automation/watchers/linkedin_session" ]; then
        echo ""
        echo "✓ LinkedIn session directory created!"
        echo "✓ Session saved to: Automation/watchers/linkedin_session/"
        echo ""
        echo "Note: If you didn't complete the login, run this script again."
        return 0
    else
        echo ""
        echo "✗ LinkedIn authentication incomplete"
        return 1
    fi
}

# Main menu
while true; do
    echo ""
    echo "=========================================="
    echo "Select which service to authenticate:"
    echo "=========================================="
    echo "1) Gmail"
    echo "2) WhatsApp"
    echo "3) LinkedIn"
    echo "4) Authenticate All (in sequence)"
    echo "5) Check Authentication Status"
    echo "6) Exit and Restart PM2 Watchers"
    echo ""
    read -p "Enter your choice (1-6): " choice

    case $choice in
        1)
            authenticate_gmail
            ;;
        2)
            authenticate_whatsapp
            ;;
        3)
            authenticate_linkedin
            ;;
        4)
            authenticate_gmail
            echo ""
            read -p "Press ENTER to continue to WhatsApp..."
            authenticate_whatsapp
            echo ""
            read -p "Press ENTER to continue to LinkedIn..."
            authenticate_linkedin
            ;;
        5)
            echo ""
            echo "=========================================="
            echo "Authentication Status"
            echo "=========================================="
            [ -f "Automation/watchers/gmail_token.pickle" ] && echo "✓ Gmail: Authenticated" || echo "✗ Gmail: Not authenticated"
            [ -d "Automation/watchers/whatsapp_session" ] && echo "✓ WhatsApp: Session exists" || echo "✗ WhatsApp: Not authenticated"
            [ -d "Automation/watchers/linkedin_session" ] && echo "✓ LinkedIn: Session exists" || echo "✗ LinkedIn: Not authenticated"
            ;;
        6)
            echo ""
            echo "Restarting PM2 watchers..."
            pm2 restart ai-watchers
            echo ""
            echo "✓ PM2 watchers restarted!"
            echo "Your watchers are now running in the background."
            echo ""
            exit 0
            ;;
        *)
            echo "Invalid choice. Please enter 1-6."
            ;;
    esac
done
