#!/usr/bin/env python3
"""
WhatsApp Authentication Debug
Shows what's actually on the page to help fix the authentication
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_whatsapp():
    """Debug WhatsApp authentication"""
    print("=" * 60)
    print("WhatsApp Authentication Debug")
    print("=" * 60)
    print()

    session_dir = Path(__file__).parent / "whatsapp_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print("Opening WhatsApp Web...")
    print()

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            executable_path='/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
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
        print("Navigating to WhatsApp Web...")
        await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)

        print("Page loaded. Waiting 10 seconds for content...")
        await asyncio.sleep(10)

        # Take screenshot
        screenshot_path = session_dir / "debug_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot saved to: {screenshot_path}")

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Get current URL
        url = page.url
        print(f"Current URL: {url}")

        # Check for common selectors
        print()
        print("Checking for common elements:")

        selectors_to_check = [
            ('QR Code (old)', 'canvas[aria-label="Scan me!"]'),
            ('QR Code (generic)', 'canvas'),
            ('Chat list (old)', '[data-testid="chat-list"]'),
            ('Chat list (generic)', '[id="pane-side"]'),
            ('Main app', '[id="app"]'),
            ('Any div', 'div'),
            ('Body', 'body'),
        ]

        for name, selector in selectors_to_check:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"  ✓ Found: {name}")
                    # Get some info about the element
                    if name.startswith('QR Code') or name.startswith('Chat list'):
                        is_visible = await element.is_visible()
                        print(f"    Visible: {is_visible}")
                else:
                    print(f"  ✗ Not found: {name}")
            except Exception as e:
                print(f"  ✗ Error checking {name}: {e}")

        print()
        print("Keeping browser open for 60 seconds so you can inspect...")
        print("If you see a QR code, scan it with your phone.")
        print("If you're already logged in, you should see your chats.")
        await asyncio.sleep(60)

        await context.close()

    finally:
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_whatsapp())
