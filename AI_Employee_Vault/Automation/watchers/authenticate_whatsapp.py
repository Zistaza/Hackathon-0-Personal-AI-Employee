#!/usr/bin/env python3
"""
WhatsApp Authentication Helper
Run this script to authenticate WhatsApp Web before running the watcher in headless mode
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def authenticate_whatsapp():
    """Authenticate WhatsApp Web and save session"""
    print("=" * 60)
    print("WhatsApp Web Authentication")
    print("=" * 60)
    print()
    print("This will open a browser window where you can scan the QR code.")
    print("After scanning, the session will be saved for headless operation.")
    print()

    session_dir = Path(__file__).parent / "whatsapp_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print(f"Session directory: {session_dir}")
    print()

    playwright = await async_playwright().start()

    try:
        # Launch browser with visible window
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to WhatsApp Web
        print("Opening WhatsApp Web...")
        await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)

        print()
        print("Waiting for authentication...")
        print()
        print("If you see a QR code:")
        print("  1. Open WhatsApp on your phone")
        print("  2. Go to Settings → Linked Devices")
        print("  3. Tap 'Link a Device'")
        print("  4. Scan the QR code on the screen")
        print()
        print("If you're already logged in, you'll see your chats.")
        print()

        # Wait for chat list to appear (indicates successful login)
        chat_selectors = [
            '[id="pane-side"]',
            '[data-testid="chat-list"]',
        ]

        print("Waiting for login (up to 5 minutes)...")

        for i in range(60):  # Check every 5 seconds for 5 minutes
            await asyncio.sleep(5)

            for selector in chat_selectors:
                element = await page.query_selector(selector)
                if element:
                    print()
                    print("✓ Authentication successful!")
                    print("✓ Session saved")
                    print()
                    print("You can now run the watcher in headless mode.")
                    print("Keeping browser open for 10 more seconds...")
                    await asyncio.sleep(10)
                    await context.close()
                    await playwright.stop()
                    return True

            if i % 6 == 0 and i > 0:  # Log every 30 seconds
                print(f"  Still waiting... ({i*5} seconds elapsed)")

        print()
        print("✗ Authentication timeout")
        print("Please try again and scan the QR code within 5 minutes.")
        await context.close()
        await playwright.stop()
        return False

    except Exception as e:
        print(f"Error: {e}")
        await playwright.stop()
        return False

if __name__ == "__main__":
    success = asyncio.run(authenticate_whatsapp())
    exit(0 if success else 1)
