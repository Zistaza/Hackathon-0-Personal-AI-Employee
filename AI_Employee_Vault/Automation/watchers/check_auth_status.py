#!/usr/bin/env python3
"""
Quick authentication status checker for all watchers
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_gmail_auth():
    """Check Gmail authentication status"""
    try:
        import pickle
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        token_file = Path(__file__).parent / "gmail_token.pickle"

        if not token_file.exists():
            return False, "Token file not found"

        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    return True, "Authenticated (token refreshed)"
                except Exception as e:
                    return False, f"Token expired and refresh failed: {e}"
            return False, "Token invalid"

        return True, "Authenticated"
    except Exception as e:
        return False, f"Error: {e}"

def check_linkedin_auth():
    """Check LinkedIn authentication status"""
    try:
        session_dir = Path(__file__).parent / "linkedin_session"

        if not session_dir.exists():
            return False, "Session directory not found"

        # Check for cookies file
        cookies_file = session_dir / "Default" / "Cookies"
        if not cookies_file.exists():
            cookies_file = session_dir / "Default" / "Network" / "Cookies"

        if cookies_file.exists():
            return True, "Session exists (needs runtime verification)"

        return False, "No cookies found in session"
    except Exception as e:
        return False, f"Error: {e}"

def check_whatsapp_auth():
    """Check WhatsApp authentication status"""
    try:
        session_dir = Path(__file__).parent / "whatsapp_session"

        if not session_dir.exists():
            return False, "Session directory not found"

        # Check for cookies or IndexedDB (WhatsApp uses IndexedDB)
        default_dir = session_dir / "Default"
        if not default_dir.exists():
            return False, "Default profile not found"

        # Check for IndexedDB or Local Storage
        indexeddb = default_dir / "IndexedDB"
        local_storage = default_dir / "Local Storage"

        if indexeddb.exists() or local_storage.exists():
            return True, "Session exists (needs runtime verification)"

        return False, "No session data found"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Check all watchers"""
    print("=" * 60)
    print("Watcher Authentication Status Check")
    print("=" * 60)
    print()

    # Check Gmail
    print("📧 Gmail Watcher:")
    status, message = check_gmail_auth()
    print(f"   Status: {'✓ ' if status else '✗ '}{message}")
    print()

    # Check LinkedIn
    print("💼 LinkedIn Watcher:")
    status, message = check_linkedin_auth()
    print(f"   Status: {'✓ ' if status else '✗ '}{message}")
    print()

    # Check WhatsApp
    print("💬 WhatsApp Watcher:")
    status, message = check_whatsapp_auth()
    print(f"   Status: {'✓ ' if status else '✗ '}{message}")
    print()

    print("=" * 60)
    print("Note: Browser-based watchers (LinkedIn, WhatsApp) require")
    print("runtime verification. Sessions may have expired.")
    print("=" * 60)

if __name__ == "__main__":
    main()
