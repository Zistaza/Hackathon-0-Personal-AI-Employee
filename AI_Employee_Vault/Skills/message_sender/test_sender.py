#!/usr/bin/env python3
"""
Test script for Message Sender v2
==================================

Validates that the sender is properly configured and can be initialized.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging


def test_sender():
    """Test Message Sender v2"""

    # Setup logging
    logger = logging.getLogger("test_sender")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    print("=" * 60)
    print("MESSAGE SENDER V2 - VALIDATION TEST")
    print("=" * 60)

    # Get base directory
    base_dir = Path(__file__).parent.parent.parent

    # Test 1: Import modules
    print("\n1. Testing module imports...")
    try:
        from Skills.message_sender.sender import MessageSenderV2
        from Skills.message_sender.platforms import (
            GmailPlatform,
            WhatsAppPlatform
        )
        print("   ✓ All modules imported successfully")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # Test 2: Initialize sender
    print("\n2. Testing sender initialization...")
    try:
        sender = MessageSenderV2(
            base_dir=base_dir,
            logger=logger
        )
        print("   ✓ Sender initialized")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False

    # Test 3: Check configuration
    print("\n3. Checking configuration...")
    config = sender.config
    if config:
        platforms = config.get('platforms', {})
        print(f"   ✓ Configuration loaded")
        print(f"   ✓ Platforms configured: {len(platforms)}")
        for platform_name, platform_config in platforms.items():
            enabled = platform_config.get('enabled', False)
            status = "✓" if enabled else "○"
            print(f"     {status} {platform_name}: {'enabled' if enabled else 'disabled'}")
    else:
        print("   ✗ Configuration not loaded")
        return False

    # Test 4: Check platform handlers
    print("\n4. Checking platform handlers...")
    for platform_name, handler in sender.platforms.items():
        print(f"   ✓ {platform_name}: {handler.__class__.__name__}")
        print(f"     - Session: {handler.session_dir}")

    # Test 5: Check directories
    print("\n5. Verifying directories...")
    directories = [
        ("Sessions", sender.sessions_dir),
        ("Logs", sender.logs_dir),
        ("Approved", sender.approved_dir),
    ]

    for name, path in directories:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {name}: {path}")

    # Test 6: Test file parsing
    print("\n6. Testing file parsing...")
    test_content = """---
platform: gmail
type: message
to: "test@example.com"
subject: "Test Subject"
content: "Test message content"
attachments: []
---

Additional content here
"""
    test_file = base_dir / "Pending_Approval" / "TEST_parse_message.md"
    try:
        test_file.write_text(test_content)
        parsed = sender.parse_message_file(test_file)

        if parsed:
            print("   ✓ File parsing works")
            print(f"     - Platform: {parsed.get('platform')}")
            print(f"     - To: {parsed.get('to')}")
            print(f"     - Subject: {parsed.get('subject')}")
            print(f"     - Content length: {len(parsed.get('content', ''))}")
        else:
            print("   ✗ File parsing failed")

        # Cleanup
        test_file.unlink()

    except Exception as e:
        print(f"   ✗ File parsing error: {e}")

    # Test 7: Check retry configuration
    print("\n7. Checking retry configuration...")
    retry_config = config.get('retry', {})
    print(f"   ✓ Max attempts: {retry_config.get('max_attempts', 3)}")
    print(f"   ✓ Initial delay: {retry_config.get('initial_delay', 5000)}ms")
    print(f"   ✓ Backoff multiplier: {retry_config.get('backoff_multiplier', 2)}")

    # Test 8: Check browser configuration
    print("\n8. Checking browser configuration...")
    browser_config = config.get('browser', {})
    print(f"   ✓ Headless: {browser_config.get('headless', False)}")
    viewport = browser_config.get('viewport', {})
    print(f"   ✓ Viewport: {viewport.get('width')}x{viewport.get('height')}")

    # Test 9: Check Gmail configuration
    print("\n9. Checking Gmail configuration...")
    gmail_config = config.get('platforms', {}).get('gmail', {})
    if gmail_config:
        print(f"   ✓ Auth method: {gmail_config.get('auth_method')}")
        print(f"   ✓ Scopes: {len(gmail_config.get('scopes', []))}")
        print(f"   ✓ Max attachments: {gmail_config.get('max_attachments')}")

        # Check for credentials file
        creds_file = base_dir / gmail_config.get('credentials_file', 'credentials.json')
        if creds_file.exists():
            print(f"   ✓ Credentials file found: {creds_file}")
        else:
            print(f"   ⚠ Credentials file not found: {creds_file}")
            print("     (Required for Gmail sending - download from Google Cloud Console)")

    # Test 10: Check WhatsApp configuration
    print("\n10. Checking WhatsApp configuration...")
    whatsapp_config = config.get('platforms', {}).get('whatsapp', {})
    if whatsapp_config:
        print(f"   ✓ URL: {whatsapp_config.get('url')}")
        selectors = whatsapp_config.get('selectors', {})
        print(f"   ✓ Selectors configured: {len(selectors)}")
        timeouts = whatsapp_config.get('timeouts', {})
        print(f"   ✓ Timeouts configured: {len(timeouts)}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✓ Message Sender v2 is properly configured!")
    print("\nNext steps:")
    print("1. Set up Gmail API credentials (credentials.json)")
    print("2. Run sender manually to authenticate Gmail")
    print("3. Run sender manually to authenticate WhatsApp (QR code)")
    print("4. Create message files in /Pending_Approval")
    print("5. Move to /Approved for sending")
    print("6. Check /Done or /Failed for results")

    return True


if __name__ == "__main__":
    try:
        success = test_sender()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
