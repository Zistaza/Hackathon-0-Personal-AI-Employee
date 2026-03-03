#!/usr/bin/env python3
"""
Quick authentication test for both LinkedIn and WhatsApp
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_watcher import LinkedInWatcher
from whatsapp_watcher import WhatsAppWatcher

async def test_linkedin():
    """Test LinkedIn authentication"""
    print("\n" + "="*60)
    print("Testing LinkedIn Authentication")
    print("="*60)

    watcher = LinkedInWatcher(headless=False)
    success = watcher.initialize()

    if success:
        print("✓ LinkedIn authentication SUCCESSFUL")
    else:
        print("✗ LinkedIn authentication FAILED")

    watcher.cleanup()
    return success

async def test_whatsapp():
    """Test WhatsApp authentication"""
    print("\n" + "="*60)
    print("Testing WhatsApp Authentication")
    print("="*60)

    watcher = WhatsAppWatcher(headless=False)
    success = watcher.initialize()

    if success:
        print("✓ WhatsApp authentication SUCCESSFUL")
    else:
        print("✗ WhatsApp authentication FAILED")

    watcher.cleanup()
    return success

def main():
    """Run authentication tests"""
    print("\nAuthentication Test Suite")
    print("This will test both LinkedIn and WhatsApp authentication")
    print("Browser windows will open - please login if prompted\n")

    # Test LinkedIn
    linkedin_ok = asyncio.run(test_linkedin())

    # Test WhatsApp
    whatsapp_ok = asyncio.run(test_whatsapp())

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"LinkedIn:  {'✓ PASS' if linkedin_ok else '✗ FAIL'}")
    print(f"WhatsApp:  {'✓ PASS' if whatsapp_ok else '✗ FAIL'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
