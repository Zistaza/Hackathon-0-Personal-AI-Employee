#!/usr/bin/env python3
"""Quick test to check if WhatsApp session is valid"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_session():
    session_dir = Path(__file__).parent / "whatsapp_session"

    print("Testing WhatsApp session...")

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=True,
            viewport={'width': 1280, 'height': 720},
            args=['--disable-blink-features=AutomationControlled']
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(10)

        # Check for chat list
        chat_element = await page.query_selector('[id="pane-side"]')

        if chat_element:
            print("✓ Session is valid - WhatsApp is authenticated")
            await context.close()
            await playwright.stop()
            return True
        else:
            print("✗ Session is invalid - Re-authentication needed")
            await context.close()
            await playwright.stop()
            return False

    except Exception as e:
        print(f"✗ Error testing session: {e}")
        await playwright.stop()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_session())
    exit(0 if result else 1)
