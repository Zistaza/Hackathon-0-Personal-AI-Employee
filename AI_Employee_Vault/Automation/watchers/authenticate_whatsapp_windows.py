#!/usr/bin/env python3
"""
WhatsApp Authentication - Windows Compatible
Run this from Windows (not WSL) to authenticate WhatsApp
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def authenticate():
    # Use Windows path
    session_dir = Path(__file__).parent / "whatsapp_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("WhatsApp Web Authentication")
    print("=" * 60)
    print(f"\nSession directory: {session_dir}\n")

    playwright = await async_playwright().start()

    try:
        # Use Chrome executable on Windows
        context = await playwright.chromium.launch_persistent_context(
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            args=['--disable-blink-features=AutomationControlled']
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening WhatsApp Web...")
        await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)

        print("\n" + "=" * 60)
        print("SCAN THE QR CODE NOW")
        print("=" * 60)
        print("1. Open WhatsApp on your phone")
        print("2. Go to Settings → Linked Devices")
        print("3. Tap 'Link a Device'")
        print("4. Scan the QR code in the browser window")
        print("\nWaiting for authentication (up to 5 minutes)...\n")

        # Wait for chat list
        for i in range(60):
            await asyncio.sleep(5)

            chat = await page.query_selector('[id="pane-side"]')
            if chat:
                print("\n✓ Authentication successful!")
                print("✓ Session saved")
                print("\nYou can now close this window and run the watcher.")
                await asyncio.sleep(5)
                await context.close()
                await playwright.stop()
                return True

            if i % 6 == 0 and i > 0:
                print(f"  Still waiting... ({i*5}s elapsed)")

        print("\n✗ Timeout - Please try again")
        await context.close()
        await playwright.stop()
        return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        await playwright.stop()
        return False

if __name__ == "__main__":
    result = asyncio.run(authenticate())
    input("\nPress Enter to exit...")
    exit(0 if result else 1)
