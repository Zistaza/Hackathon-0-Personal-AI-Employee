#!/bin/bash
# Gmail Manual Authentication Helper
# This script generates the OAuth URL for you to open in Windows browser

cd "/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault"
source .venv/bin/activate

echo "=========================================="
echo "Gmail Manual Authentication"
echo "=========================================="
echo ""
echo "Since WSL can't open browsers automatically, we'll do this manually."
echo ""

cd Automation/watchers

python3 << 'PYTHON_SCRIPT'
import sys
import os
sys.path.insert(0, '.')

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

print("Generating Gmail OAuth URL...")
print("")

flow = InstalledAppFlow.from_client_secrets_file(
    '../../credentials.json',
    SCOPES,
    redirect_uri='http://localhost:8080/'
)

auth_url, _ = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true'
)

print("=" * 60)
print("STEP 1: Copy this URL and paste it in your Windows browser:")
print("=" * 60)
print("")
print(auth_url)
print("")
print("=" * 60)
print("")
print("STEP 2: After you authorize:")
print("  - Google will redirect to localhost:8080")
print("  - Your browser will show 'This site can't be reached'")
print("  - Copy the ENTIRE URL from your browser address bar")
print("  - It will look like: http://localhost:8080/?code=4/0A...")
print("")
print("=" * 60)
print("")

callback_url = input("Paste the callback URL here: ").strip()

if not callback_url or 'code=' not in callback_url:
    print("")
    print("✗ Invalid URL. Please run this script again.")
    sys.exit(1)

print("")
print("Exchanging code for token...")

try:
    flow.fetch_token(authorization_response=callback_url)
    credentials = flow.credentials

    # Save the credentials
    import pickle
    with open('./gmail_token.pickle', 'wb') as token:
        pickle.dump(credentials, token)

    print("")
    print("✓ Gmail authentication successful!")
    print("✓ Token saved to: Automation/watchers/gmail_token.pickle")
    print("")

except Exception as e:
    print("")
    print(f"✗ Authentication failed: {e}")
    print("")
    sys.exit(1)

PYTHON_SCRIPT

cd ../..
