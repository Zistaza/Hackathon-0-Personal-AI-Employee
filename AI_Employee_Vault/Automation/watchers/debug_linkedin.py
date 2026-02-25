#!/usr/bin/env python3
"""
LinkedIn Authentication Debug
Shows what's actually on the page to help fix the authentication
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_linkedin():
    """Debug LinkedIn authentication"""
    print("=" * 60)
    print("LinkedIn Authentication Debug")
    print("=" * 60)
    print()

    session_dir = Path(__file__).parent / "linkedin_session"
    session_dir.mkdir(parents=True, exist_ok=True)

    print("Opening LinkedIn...")
    print()

    playwright = await async_playwright().start()

    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to LinkedIn
        await page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')

        print("Page loaded. Waiting 5 seconds...")
        await asyncio.sleep(5)

        # Take screenshot
        screenshot_path = session_dir / "debug_screenshot.png"
        await page.screenshot(path=str(screenshot_path))
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
            ('Login form', 'input[name="session_key"]'),
            ('Feed container', '[data-test-id="feed-container"]'),
            ('Feed', 'main[role="main"]'),
            ('Navigation', 'nav'),
            ('Profile link', 'a[href*="/in/"]'),
            ('Any input', 'input'),
            ('Any button', 'button'),
        ]

        for name, selector in selectors_to_check:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"  ✓ Found: {name}")
                else:
                    print(f"  ✗ Not found: {name}")
            except Exception as e:
                print(f"  ✗ Error checking {name}: {e}")

        print()
        print("Keeping browser open for 30 seconds so you can inspect...")
        print("Check if you're logged in and on the feed page.")
        await asyncio.sleep(30)

        await context.close()

    finally:
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_linkedin())
